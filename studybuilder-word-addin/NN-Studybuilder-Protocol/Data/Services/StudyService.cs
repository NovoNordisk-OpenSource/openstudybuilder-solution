using NN_Studybuilder_Protocol.Data.Repositories;
using NN_Studybuilder_Protocol.StudybuildApi;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Data.Services
{
    public class StudyService
    {
        private readonly StudyRepository studyRepository;

        public StudyService(StudyRepository studyRepository)
        {
            this.studyRepository = studyRepository;
        }

        public async Task<IEnumerable<StudyDto>> GetStudies()
        {
            return await studyRepository.GetAll();
        }

        public async Task<IEnumerable<StudyDto>> Search(string q)
        {
            return await studyRepository.Search(q);
        }

        public async Task<Clinical_mdr_api__models__study_selections__study__Study> GetStudy(string uid, string version = null)
        {
            return await studyRepository.GetStudyById(uid, version);
        }

        public async Task<IEnumerable<StudySelectionObjective>> GetStudySelectionObjective(string studyUid)
        {
            return await studyRepository.GetStudySelectionObjective(studyUid);
        }

        public async Task<IEnumerable<EndpointDto>> GetStudyObjectiveEndpoints(string studyUid)
        {
            return await studyRepository.GetStudyEndpoints(studyUid);
        }

        public async Task<ProtocolTitleDto> GetProtocolTitleDto(string studyUid, string version = null)
        {
            return await studyRepository.GetProtocolTitle(studyUid, version);
        }

        public async Task<byte[]> GetFlowchart(string studyUid)
        {
            return await studyRepository.GetFlowchart(studyUid);
        }

        public async Task<IEnumerable<StudySelectionCriteria>> GetInclusionCriteria(string studyUid, string version = null)
        {
            return await studyRepository.GetInclusionCriteria(studyUid, version);
        }

        public async Task<IEnumerable<StudySelectionCriteria>> GetExclusionCriteria(string studyUid, string version = null)
        {
            return await studyRepository.GetExclusionCriteria(studyUid, version);
        }

        public async Task<byte[]> GetObjectivesEndpoints(string studyUid, string version = null)
        {
            return await studyRepository.GetObjectivesEndpoints(studyUid, version);
        }

        public async Task<IEnumerable<StudyVersionDto>> GetStudyVersions(string studyUid)
        {
            var result = await studyRepository.GetStudyVersions(studyUid);
            return result.Select(v => new StudyVersionDto { Version = v.VersionNumber, Status = v.Status, VersionDate = v.VersionTimestamp })
            .ToList();
        }

        public async Task<byte[]> GetStudyDesign(string studyUid, string version = null)
        {
            return await studyRepository.GetStudyDesign(studyUid, version);
        }
    }
}
