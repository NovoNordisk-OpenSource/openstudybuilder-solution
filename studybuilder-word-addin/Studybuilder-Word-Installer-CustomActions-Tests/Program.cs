using Studybuilder_Word_Installer_CustomActions;
using System.IO;

namespace Studybuilder_Word_Installer_CustomActions_Tests
{
    class Program
    {
        static void Main(string[] args)
        {
            var settingsFolder = @"C:\Users\JacobHoerbyeJensenPo\source\repos\NN_Studybuilder_addin\NN-Studybuilder-Protocol\bin\Debug";
            var settingsFilename = "NN.Studybuilder.Protocol.dll.config";

            var clientId = "cid";
            var tenantId = "tid";
            var scopes = "scp";
            var url = "uri";

            var targetExe = Path.Combine(settingsFolder, settingsFilename);
            var appConfig = new VstoSettingsReader(targetExe);
            appConfig.Set("Studybuilder_ClientId", clientId);
            appConfig.Set("Studybuilder_TenantId", tenantId);
            appConfig.Set("Studybuilder_Scopes", scopes);
            appConfig.Set("ApiUrl", url);

            appConfig.Save();
        }
    }
}
