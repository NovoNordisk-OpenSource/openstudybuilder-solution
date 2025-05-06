import 'vuetify/styles'
import '@/styles/global.scss'
import '@mdi/font/css/materialdesignicons.css'
import { createVuetify } from 'vuetify'
// import * as components from 'vuetify/components'
// import * as directives from 'vuetify/directives'
// import { aliases, mdi } from 'vuetify/iconsets/mdi'

const NNCustomLightTheme = {
  dark: false,
  colors: {
    primary: '#193074',
    secondary: '#0066F8',
    accent: '#2196f3',
    error: '#f44336',
    warning: '#EAAB00',
    info: '#0a56c2',
    success: '#4caf50',
    green: '#3f9c35',
    red: '#e6553f',
    orange: '#FF9800',
    dfltBackground: '#f2f7fd',
    dfltBackgroundLight1: '#B1D5F2',
    dfltBackgroundLight2: '#D8EAF8',
    greyBackground: '#ebe8e5',
    nnLightBlue1: '#334784',
    nnLightBlue2: '#6675a3',
    nnLightBlue4: '#e5e8ef',
    nnDarkBlue1: '#2267c8',
    nnGreen1: '#2a918b',
    nnPink1: '#eea7bf',
    parameterBackground: '#E0E0E0',
    crfTemplate: '#193074',
    crfForm: '#005AD2',
    crfGroup: '#3B97DE',
    crfItem: '#63A8A5',
    darkGrey: '#747474',
    tableGray: '#E5E5E5',
    // Novo Design color palette
    nnWhite: '#FFFFFF',
    nnBaseBlue: '#005BD2',
    nnTrueBlue: '#001965',
    nnBaseGray: '#939AA7',
    nnBaseHeavy: '#E8EAF0',
    nnBaseLight: '#F7F8FA',
    nnGray200: '#E9EAED',
    nnGray300: '#D3D6DB',
    nnSeaBlue100: '#E5F1FF',
    nnSeaBlue200: '#CCE2FF',
    nnSeaBlue300: '#99C5FF',
    nnSeaBlue400: '#66A8FF',
    nnSeaBlue700: '#0049A9',
    nnSeaBlue900: '#002C66',
    nnLightBlue100: '#F4F5F8',
    nnLightBlue200: '#D7EAF8',
    nnFadedBlue200: '#DEE1EB',
    nnGoldenSun200: '#FAEECC',
    nnGraniteGrey1: '#f4f5f6',
  },
}

export default createVuetify({
  theme: {
    defaultTheme: 'NNCustomLightTheme',
    themes: {
      NNCustomLightTheme,
    },
  },
})
