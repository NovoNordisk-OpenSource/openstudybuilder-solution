import api from '../libraryObjects'
import utils from '../utils'

const basePath = 'concepts/pharmaceutical-products'

const pharmaceuticalProducts = api(basePath)

const pageSize = 100

export default {
  ...pharmaceuticalProducts,
  getPharmaProducts() {
    return utils.getAllPaginatedItems(basePath, pageSize)
  },
}
