const categoryActivityItemClasses = {
  CategoricFindings: 'finding_category',
  NumericFindings: 'finding_category',
  TextualFindings: 'finding_category',
  Events: 'event_category',
  Interventions: 'intervention_category',
}

const subcategoryActivityItemClasses = {
  CategoricFindings: 'finding_subcategory',
  NumericFindings: 'finding_subcategory',
  TextualFindings: 'finding_subcategory',
  Events: 'event_subcategory',
  Interventions: 'intervention_subcategory',
}

const codelistsPerDomain = {
  BS: {
    test_code: ['BSTESTCD'],
    test_name: ['BSTEST'],
  },
  CC: {
    finding_category: ['CCCAT'],
  },
  CV: {
    test_code: ['CVTESTCD'],
    test_name: ['CVTEST'],
  },
  DA: {
    test_code: ['DATESTCD'],
    test_name: ['DATEST'],
  },
  DO: {
    test_code: ['DOTESTCD'],
    test_name: ['DOTEST'],
  },
  DU: {
    test_code: ['DUTESTCD'],
    test_name: ['DUTEST'],
  },
  DD: {
    test_code: ['DDTESTCD'],
    test_name: ['DDTEST'],
  },
  EG: {
    test_code: ['EGTESTCD'],
    test_name: ['EGTEST'],
    finding_category: ['EGCAT'],
  },
  FT: {
    test_code: ['FTTESTCD'],
    test_name: ['FTTEST'],
  },
  IE: {
    finding_category: ['IECAT'],
    test_code: ['IETESTCD'],
    test_name: ['IETEST'],
  },
  IS: {
    test_code: ['ISTESTCD'],
    test_name: ['ISTEST'],
  },
  MB: {
    test_code: ['MBTESTCD'],
    test_name: ['MBTEST'],
  },
  MI: {
    test_code: ['MITESTCD'],
    test_name: ['MITEST'],
  },
  MK: {
    test_code: ['MKTESTCD'],
    test_name: ['MKTEST'],
  },
  MO: {
    test_code: ['MOTESTCD'],
    test_name: ['MOTEST'],
  },
  MS: {
    test_code: ['MSTESTCD'],
    test_name: ['MSTEST'],
  },
  NV: {
    test_code: ['EGTESTCD'],
    test_name: ['EGTEST'],
  },
  OE: {
    finding_category: ['OECAT'],
    test_code: ['OETESTCD'],
    test_name: ['OETEST'],
  },
  PC: {
    test_code: ['PCTESTCD'],
    test_name: ['PCTEST'],
  },
  PE: {
    finding_category: ['PECAT'],
    test_code: ['PETESTCD'],
    test_name: ['PETEST'],
  },
  PF: {
    test_code: ['PFTESTCD'],
    test_name: ['PFTEST'],
  },
  RE: {
    test_code: ['RETESTCD'],
    test_name: ['RETEST'],
  },
  SR: {
    test_code: ['SRTESTCD'],
    test_name: ['SRTEST'],
  },
  SS: {
    test_code: ['SSTESTCD'],
    test_name: ['SSTEST'],
  },
  TR: {
    test_code: ['TRTESTCD'],
    test_name: ['TRTEST'],
  },
  TU: {
    test_code: ['TUTESTCD'],
    test_name: ['TUTEST'],
  },
  UR: {
    test_code: ['URTESTCD'],
    test_name: ['URTEST'],
  },
  XA: {
    test_code: ['XATESTCD'],
    test_name: ['XATEST'],
  },
  XS: {
    test_code: ['XSTESTCD'],
    test_name: ['XSTEST'],
  },
  ZI: {
    test_code: ['ZITESTCD'],
    test_name: ['ZITEST'],
  },
  FA: {
    test_code: ['FATESTCD'],
    test_name: ['FATEST'],
  },
  LB: {
    test_code: ['LBTESTCD'],
    test_name: ['LBTEST'],
  },
  RP: {
    finding_category: ['RPCAT'],
    test_code: ['RPTESTCD'],
    test_name: ['RPTEST'],
  },
  RS: {
    test_code: ['RSTESTCD'],
    test_name: ['RSTEST'],
  },
  QS: {
    finding_category: ['QSCAT'],
    test_code: ['QSTESTCD'],
    test_name: ['QSTEST'],
  },
  SC: {
    test_code: ['SCTESTCD'],
    test_name: ['SCTEST'],
  },
  VS: {
    test_code: ['VSTESTCD'],
    test_name: ['VSTEST'],
    finding_category: ['VSCAT'],
  },
  ZA: {
    test_code: ['ZATESTCD'],
    test_name: ['ZATEST'],
  },
}

export default {
  categoryActivityItemClasses,
  subcategoryActivityItemClasses,
  codelistsPerDomain,
}
