using Newtonsoft.Json;

namespace NN_Studybuilder_Protocol.Data
{
    public class ProtocolTitleDto
    {
        [JsonProperty("study_uid")]
        public string StudyUid { get; set; }

        [JsonProperty("study_title")]        
        public string StudyTitle { get; set; }

        [JsonProperty("eudract_id")]
        public string EudractId { get; set; }

        [JsonProperty("universal_trial_number_utn")]
        public string UniversalTrialNumberUTN { get; set; }

        [JsonProperty("ind_number")]
        public string IndNumber { get; set; }

        [JsonProperty("substance_name")]
        public string SubstanceName { get; set; }

        [JsonProperty("trial_phase_code")]
        public TrialPhaseCodeDto TrialPhaseCode { get; set; }

        [JsonProperty("study_short_title")]
        public string StudyShortTitle { get; set; }
    }
}
