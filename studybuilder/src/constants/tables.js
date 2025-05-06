import { i18n } from '@/plugins/i18n'
const ITEMS_PER_PAGE_OPIONS = [
  {
    value: 5,
    title: '5',
  },
  {
    value: 10,
    title: '10',
  },
  {
    value: 15,
    title: '15',
  },
  {
    value: 25,
    title: '25',
  },
  {
    value: 50,
    title: '50',
  },
  {
    value: 100,
    title: '100',
  },
  {
    value: -1,
    title: i18n.t('_global.all'),
  },
]

export default {
  ITEMS_PER_PAGE_OPIONS,
}
