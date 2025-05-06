using System.Collections.Generic;

namespace NN_Studybuilder_Protocol.Data.Repositories
{
    public class StudyBuilderApiEnvironmentRepository
    {
        private readonly ConfigManager configManager;

        public StudyBuilderApiEnvironmentRepository(ConfigManager configManager)
        {
            this.configManager = configManager;
        }

        public IEnumerable<StudyBuilderApiEnvironment> GetEnvironments()
        {
            return new StudyBuilderApiEnvironment[0];            
        }

        public void Save(StudyBuilderApiEnvironment studyBuilderApiEnvironment)
        {
            configManager.StudyBuilder_ApiUrl = studyBuilderApiEnvironment.Url;
            configManager.StudyBuilder_ClientId = studyBuilderApiEnvironment.ClientId;
            configManager.StudyBuilder_Scopes = studyBuilderApiEnvironment.Scopes;
            configManager.StudyBuilder_TenantId = studyBuilderApiEnvironment.TenantId;

            configManager.SaveSettings();
        }

        public string GetActiveEnvironmentUrl()
        {
            return configManager.StudyBuilder_ApiUrl;
        }
    }
}
