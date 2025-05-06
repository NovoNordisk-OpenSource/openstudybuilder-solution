using NN_Studybuilder_Protocol.StudybuildApi;
using System.Collections.Generic;

namespace NN_Studybuilder_Protocol.Data.StudybuilderApi
{
    public class StudiesDto
    {
        public int total { get; set; }
        public int page { get; set; }
        public int size { get; set; }
        public List<Clinical_mdr_api__models__study_selections__study__Study> items { get; set; }
    }
}
