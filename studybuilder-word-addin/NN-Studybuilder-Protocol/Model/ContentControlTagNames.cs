namespace NN_Studybuilder_Protocol.Model
{
    public class ContentControlTagNames
    {
        public const string ProtocolTitle = "SB_ProtocolTitle";
        public const string Acronym = "SB_Acronym";

        
        public const string StudyTitleShort = "SB_StudyTitleShort"; // old
        public const string ProtocolTitleShort = "SB_ProtocolTitleShort"; // new

        public const string Substance = "SB_Substance"; // no content control yet

        public const string ProtocolNumber = "SB_StudyID"; // v14

        public const string UniversalTrialNumber = "SB_UniversalTrialNumber";

        public const string EudraCTNumber = "SB_EudraCTNumber"; // old, v13.x
        public const string EUTrialNumber = "SB_EUTrialNumber"; // v14

        public const string INDNumber = "SB_INDNumber";

        // Registry identifier
        public const string SB_CIVID_SIN = "SB_CIVID_SIN"; // For investigational medical devices or IVDs, state the CIV-ID number until the EUDAMED database is available whereby a SIN number is needed
        // Registry identifier
        public const string NCTnumber = "SB_NCT"; // National Clinical Trial Number, v14

        // Registry identifier        
        public const string jRCTnumber = "SB_jRCT"; // Japanese Trial Registry Number, v14

        // Registry identifier        
        public const string NMPAnumber = "SB_NMPA"; // China National Medicinal Products Administration number, v14

        // Registry identifier
        public const string EUDAMED = "SB_EUDAMED"; // v14

        // Registry identifier
        public const string IDEnumber= "SB_IDE"; // Investigational device exemption

        public const string StudyPhase = "SB_StudyPhase";
        
        public const string DevelopmentStage = "SB_Developmentstage"; // needs implementing - ready in API?

        public const string Flowchart = "SB_Flowchart"; // Schedule of Activities // Old (backwards compatible) v13
        public const string SoA = "SB_SoA"; // Schedule of Activities // New, v14

        public const string ObjectivesEndpoints = "SB_ObjectivesEndpoints"; // v13+

        public const string StudydesignGraphic = "SB_StudydesignGraphic"; // Study design figure, v14

        public const string InclusionCriteria = "SB_InclusionCriteria";
        public const string ExclusionCriteria = "SB_ExclusionCriteria";
              
    }
}
