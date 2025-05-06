using System.Collections;
using System.ComponentModel;
using System.IO;

namespace Studybuilder_Word_Installer_CustomActions
{
    [RunInstaller(true)]
    public partial class VstoSettingsInstaller : System.Configuration.Install.Installer
    {
        public VstoSettingsInstaller()
        {
            InitializeComponent();
        }

        public override void Install(IDictionary stateSaver)
        {
            base.Install(stateSaver);

            var targetDir = Context.Parameters["targetDir"];

            var clientId = Context.Parameters["clientId"];
            var tenantId = Context.Parameters["tenantId"];
            var scopes = Context.Parameters["scopes"];
            var url = Context.Parameters["url"];

            var targetConfigPath = Path.Combine(targetDir, "NN.Studybuilder.Protocol.dll.config");
            var vstoSettings = new VstoSettingsReader(targetConfigPath);
            vstoSettings.Set("Studybuilder_ClientId", clientId);
            vstoSettings.Set("Studybuilder_TenantId", tenantId);
            vstoSettings.Set("Studybuilder_Scopes", scopes);
            vstoSettings.Set("ApiUrl", url);

            vstoSettings.Save();
        } 
    }
}
