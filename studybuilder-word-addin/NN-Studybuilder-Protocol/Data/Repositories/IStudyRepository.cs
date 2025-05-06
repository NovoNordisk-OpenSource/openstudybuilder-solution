using NN_Studybuilder_Protocol.StudybuildApi;
using System;
using System.Collections.Generic;

namespace NN_Studybuilder_Protocol.Data.Repositories
{
    public interface IStudyRepository
    {
        IEnumerable<StudyDto> GetAll();
        StudyDto GetStudyById(string uid);
        IEnumerable<StudySelectionObjective> GetStudySelectionObjective(Guid studyId);
        IEnumerable<EndpointDto> GetStudyEndpoints(Guid studyId);
    }
}