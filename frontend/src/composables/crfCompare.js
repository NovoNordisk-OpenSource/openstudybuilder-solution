import crfs from '@/api/crfs'
import { normalizeCollectionTree, normalizeFormTree } from '@/utils/crfCompare'
import {
  describeApply,
  itemPatch,
  itemsWithAdded,
  itemsWithRefValues,
  itemsWithRemoved,
} from '@/utils/crfCompareApply'

const MAX_PARALLEL_REQUESTS = 6

function createLimiter(max) {
  let active = 0
  const waiting = []
  const release = () => {
    active--
    waiting.shift()?.()
  }
  return async (task) => {
    if (active >= max) {
      await new Promise((resolve) => waiting.push(resolve))
    }
    active++
    try {
      return await task()
    } finally {
      release()
    }
  }
}

export function useCrfCompare() {
  function versionsOf(resp) {
    const versions = new Map()
    for (const entry of resp.data) {
      if (!versions.has(entry.version)) {
        versions.set(entry.version, entry.status)
      }
    }
    return [...versions].map(([version, status]) => ({ version, status }))
  }

  async function loadFormVersions(uid) {
    return versionsOf(await crfs.getFormAuditTrail(uid))
  }

  // The API has no single call for a whole form, so loading one fans out.
  // The memo is shared by everything loaded through one call.
  function createFetcher() {
    const limit = createLimiter(MAX_PARALLEL_REQUESTS)
    const memo = new Map()
    return (kind, elementUid, elementVersion, fetcher) => {
      const key = `${kind}:${elementUid}:${elementVersion}`
      if (!memo.has(key)) {
        memo.set(
          key,
          limit(() => fetcher(elementUid, elementVersion)).then(
            (resp) => resp.data
          )
        )
      }
      return memo.get(key)
    }
  }

  async function fetchFormTree(once, uid, version) {
    const form = await once('form', uid, version, crfs.getForm)
    const groups = await Promise.all(
      form.item_groups.map(async (ref) => {
        const group = await once(
          'group',
          ref.uid,
          ref.version,
          crfs.getItemGroup
        )
        const items = await Promise.all(
          group.items.map(async (itemRef) => ({
            ref: itemRef,
            item: await once(
              'item',
              itemRef.uid,
              itemRef.version,
              crfs.getItem
            ),
          }))
        )
        return { ref, group, items }
      })
    )
    return { form, groups }
  }

  // Loads a form at one version together with every item group and item it
  // references at the version the form pins, and returns it normalized for
  // comparison.
  async function loadForm(uid, version) {
    return normalizeFormTree(await fetchFormTree(createFetcher(), uid, version))
  }

  async function loadCollectionVersions(uid) {
    return versionsOf(await crfs.getCollectionAuditTrail(uid))
  }

  // Loads a collection at one version with all of its forms, each at the
  // version the collection pins.
  async function loadCollection(uid, version) {
    const once = createFetcher()
    const collection = await once(
      'collection',
      uid,
      version,
      crfs.getCollection
    )
    const forms = await Promise.all(
      [...collection.forms]
        .sort((a, b) => (a.order_number ?? 0) - (b.order_number ?? 0))
        .map((ref) => fetchFormTree(once, ref.uid, ref.version))
    )
    return normalizeCollectionTree({ collection, forms })
  }

  // Parses an ODM XML file on the server (nothing is stored) and returns one
  // normalized form per FormDef in it. File elements carry synthetic uids (the
  // OID) and version 'file'; libraryName is the file name, shown in the header.
  async function loadFile(file, { mapperFile, exporter } = {}) {
    const resp = await crfs.parseOdmXml(file, { mapperFile, exporter })
    return (resp.data.forms || []).map((tree) => ({
      ...normalizeFormTree(tree),
      libraryName: file.name,
      version: 'file',
      fromFile: true,
    }))
  }

  // A file with several FormDefs, compared in Collections mode, behaves like a
  // collection made of those forms.
  function fileAsCollection(file, forms) {
    return {
      uid: `file:${file.name}`,
      name: file.name,
      libraryName: file.name,
      version: 'file',
      fromFile: true,
      forms,
    }
  }

  const SIDES = {
    toRight: ['left', 'right'],
    toLeft: ['right', 'left'],
  }

  // A shown version can only be edited if it is the latest one: edits land on
  // the latest version of an element, which is what the other form may be using
  // too. Returns an i18n key under CRFCompare.cannot_apply, or null when fine.
  // sources is { left, right }, each 'db' or 'file'.
  async function checkApply(row, groupRow, direction, sources) {
    const [from, to] = SIDES[direction]
    // File elements have no DB uids, so nothing can be read from or written to.
    if (sources?.[from] === 'file') return 'source_is_file'
    if (sources?.[to] === 'file') return 'target_is_file'
    const targetGroup = groupRow[to]
    if (!targetGroup) return 'no_target_group'
    const desc = describeApply(row, direction)
    const touchesItem = desc.kind === 'update' && desc.itemFields.size > 0
    const touchesGroup = desc.kind !== 'update' || desc.refFields.size > 0
    if (touchesItem) {
      const latest = (await crfs.getItem(row[to].uid)).data
      if (latest.version !== row[to].version) return 'item_not_latest'
    }
    if (touchesGroup) {
      const latest = (await crfs.getItemGroup(targetGroup.uid)).data
      if (latest.version !== targetGroup.version) return 'group_not_latest'
    }
    return null
  }

  async function draftOf(kind, uid) {
    const latest = (
      await (kind === 'items' ? crfs.getItem(uid) : crfs.getItemGroup(uid))
    ).data
    if (latest.status === 'Draft') return latest
    return (await crfs.newVersion(kind, uid)).data
  }

  // Copies what differs in one item row from one form onto the other, creating
  // a new draft of the target item / group first when it is not one already.
  async function applyItemRow(row, groupRow, direction, options) {
    const [from, to] = SIDES[direction]
    const source = row[from]
    const target = row[to]
    const targetGroup = groupRow[to]
    const desc = describeApply(row, direction)

    if (desc.kind === 'add') {
      const group = await draftOf('item-groups', targetGroup.uid)
      await crfs.addItemsToItemGroup(
        itemsWithAdded(group.items, { ...source.ref, uid: source.uid }),
        targetGroup.uid,
        true
      )
    } else if (desc.kind === 'remove') {
      const group = await draftOf('item-groups', targetGroup.uid)
      await crfs.addItemsToItemGroup(
        itemsWithRemoved(group.items, target.uid),
        targetGroup.uid,
        true
      )
    } else {
      if (desc.itemFields.size > 0) {
        const draft = await draftOf('items', target.uid)
        await crfs.updateItem(
          itemPatch(draft, source.raw, desc.itemFields, options),
          target.uid
        )
      }
      if (desc.refFields.size > 0) {
        const group = await draftOf('item-groups', targetGroup.uid)
        await crfs.addItemsToItemGroup(
          itemsWithRefValues(
            group.items,
            target.uid,
            source.ref,
            desc.refFields
          ),
          targetGroup.uid,
          true
        )
      }
    }
  }

  return {
    loadForm,
    loadFormVersions,
    loadCollection,
    loadCollectionVersions,
    loadFile,
    fileAsCollection,
    checkApply,
    applyItemRow,
  }
}
