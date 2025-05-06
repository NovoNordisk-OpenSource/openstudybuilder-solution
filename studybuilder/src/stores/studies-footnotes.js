import { defineStore } from 'pinia'
import footnotes from '@/api/footnotes'
import study from '@/api/study'
import instances from '@/utils/instances'
import utils from '@/stores/utils'

export const useFootnotesStore = defineStore('footnotes', {
  state: () => ({
    studyFootnotes: [],
    total: 0,
  }),

  actions: {
    fetchStudyFootnotes(data) {
      const studyUid = data.studyUid
      delete data.studyUid
      return study.getStudyFootnotes(studyUid, data).then((resp) => {
        this.studyFootnotes = resp.data.items
        this.total = resp.data.total
        return resp
      })
    },
    /*
     ** Create a study footnote based on an footnote template. We fist
     ** look if an footnote already exists for the provided name. If so,
     ** we select it, otherwise we create a new footnote in Final state
     ** and select if.
     */
    async addStudyFootnoteFromTemplate({
      studyUid,
      form,
      parameters,
      referencedItems,
    }) {
      const footnote = {
        footnote_template_uid: form.footnote_template.uid,
        parameter_terms: await instances.formatParameterValues(parameters),
        library_name: form.footnote_template.library.name,
      }
      const data = {
        footnote_data: footnote,
        referenced_items: referencedItems,
      }
      return study.createStudyFootnote(studyUid, data, true)
    },
    selectFromStudyFootnote({ studyUid, footnoteUid, referencedItems }) {
      return study.selectStudyFootnote(studyUid, footnoteUid, referencedItems)
    },
    async updateStudyFootnote({
      studyUid,
      studyFootnoteUid,
      form,
      template,
      library,
    }) {
      const data = {}
      let footnoteUid = null

      // Search for an existing footnote by name
      const searchName = await utils.getInternalApiName(
        template.name,
        form.parameters
      )
      const response = await footnotes.getObjectByName(searchName)
      if (response.data.items.length && response.data.items.length > 0) {
        footnoteUid = response.data.items[0].uid
      } else {
        // Create footnote since an footnote with specified name does not exist
        const footnote = {
          footnote_template_uid: template.uid,
          parameter_terms: form.parameters
            ? await instances.formatParameterValues(form.parameters)
            : [],
          library_name: library.name,
        }
        const resp = await footnotes.create(footnote)
        footnoteUid = resp.data.uid
        await footnotes.approve(footnoteUid)
      }
      data.footnote_uid = footnoteUid
      await study.updateStudyFootnote(studyUid, studyFootnoteUid, data)
    },
    async updateStudyFootnoteLatestVersion(studyUid, studyFootnoteUid) {
      const resp = await study.updateStudyFootnoteLatestVersion(
        studyUid,
        studyFootnoteUid
      )
      this.studyFootnotes.filter((item, pos) => {
        if (item.study_objective_uid === resp.data.study_objective_uid) {
          this.studyFootnotes[pos] = resp.data
          return true
        }
        return false
      })
    },
    async updateStudyFootnoteAcceptVersion(studyUid, studyFootnoteUid) {
      const resp = await study.updateStudyFootnoteAcceptVersion(
        studyUid,
        studyFootnoteUid
      )
      this.studyFootnotes.filter((item, pos) => {
        if (item.study_objective_uid === resp.data.study_objective_uid) {
          this.studyFootnotes[pos] = resp.data
          return true
        }
        return false
      })
    },
    deleteStudyFootnote(studyUid, studyFootnoteUid) {
      return study.deleteStudyFootnote(studyUid, studyFootnoteUid).then(() => {
        this.studyFootnotes = this.studyFootnotes.filter(function (item) {
          return item.study_footnote_uid !== studyFootnoteUid
        })
      })
    },
    updateStudyFootnoteVersion(studyUid, studyFootnoteUid) {
      return study.updateStudyFootnoteVersion(studyUid, studyFootnoteUid)
    },
    acceptStudyFootnoteVersion(studyUid, studyFootnoteUid) {
      return study.acceptStudyFootnoteVersion(studyUid, studyFootnoteUid)
    },
  },
})
