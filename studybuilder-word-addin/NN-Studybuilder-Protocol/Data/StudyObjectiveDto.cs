using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Data
{
    public class StudyObjectiveDto
    {
        public string studyObjectiveUid { get; set; }
        public string studyUid { get; set; }
        public string objectiveLevel { get; set; }
        public int order { get; set; }


    }
}
