using Microsoft.Identity.Client;
using Microsoft.Identity.Client.Extensions.Msal;
using System.Linq;
using System.Threading.Tasks;

namespace NN_Studybuilder_Protocol.Data.Services
{
    public class PublicClientAppFactory
    {
        private readonly ConfigManager configManager;
        private IPublicClientApplication cachedClientApp;

        public PublicClientAppFactory(ConfigManager configManager)
        {
            this.configManager = configManager;
        }

        public void ResetCachedClientApp()
        {
            if (cachedClientApp != null)
            {
                var a = cachedClientApp.GetAccountsAsync().Result.FirstOrDefault();
                if (a != null)
                {
                    cachedClientApp.RemoveAsync(a);
                }
                cachedClientApp = null;
            }
        }

        public async Task<IPublicClientApplication> Create()
        {
            // Check if we already have a cached instance and if its configuration matches the current config
            if (cachedClientApp != null
                && configManager.StudyBuilder_ClientId == cachedClientApp.AppConfig.ClientId
                && configManager.StudyBuilder_Authority == cachedClientApp.Authority)
            {
                return cachedClientApp;
            }

            cachedClientApp = PublicClientApplicationBuilder
                 .Create(configManager.StudyBuilder_ClientId)
                 .WithAuthority(configManager.StudyBuilder_Authority)
                 .WithDefaultRedirectUri()
                 .Build();

            var cacheHelper = await CreateCacheHelperAsync();
            cacheHelper.RegisterCache(cachedClientApp.UserTokenCache);

            return cachedClientApp;
        }

        private static async Task<MsalCacheHelper> CreateCacheHelperAsync()
        {
            // Since this is a Desktop application, only Windows storage is configured
            var storageProperties = new StorageCreationPropertiesBuilder(
                              System.Reflection.Assembly.GetExecutingAssembly().GetName().Name + ".msalcache.bin",
                              MsalCacheHelper.UserRootDirectory)
                                .Build();

            return await MsalCacheHelper.CreateAsync(storageProperties).ConfigureAwait(false);
        }
    }
}
