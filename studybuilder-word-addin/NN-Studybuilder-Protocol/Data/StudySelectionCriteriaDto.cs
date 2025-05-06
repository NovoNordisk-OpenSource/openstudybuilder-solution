using NN_Studybuilder_Protocol.StudybuildApi;
using System.Collections.Generic;

namespace NN_Studybuilder_Protocol.Data
{
    public class StudySelectionCriteriaDto
    {
        public int total { get; set; }
        public int page { get; set; }
        public int size { get; set; }
        public List<StudySelectionCriteria> items { get; set; }
    }  
}
