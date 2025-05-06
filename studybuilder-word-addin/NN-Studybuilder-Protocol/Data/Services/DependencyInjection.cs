using NN_Studybuilder_Protocol.Controls.CustomPanes;
using NN_Studybuilder_Protocol.Data.Repositories;
using SimpleInjector;
using SimpleInjector.Diagnostics;
using System.Net.Http;

namespace NN_Studybuilder_Protocol.Data.Services
{
    public class DependencyInjection
    {
        private Container container;

        public void RegisterServices()
        {
            container = new Container();

            container.RegisterSingleton<HttpClientHandler>();
            container.RegisterSingleton<ConfigManager>();
            container.RegisterSingleton<PublicClientAppFactory>();
            container.Register<AuthenticationRepository>();

            container.Register<ContentControlManager>();
            container.Register<StudyService>();
            container.Register<StudyRepository>();
            container.Register<StudybuilderApiFactory>();
            container.Register<TemplateUpdateService>();
            container.Register<FileHandler>();
            container.Register<GetOrRefreshDataUserControl>();
            container.Register<StudyBuilderNavigatorUserControl>();
            container.Register<NetworkService>();
            container.Register<CustomTaskPaneDisplayManager>();

            // Dispose is handled by the .net framework, so we suppress this warning here
            Registration registration2 = container.GetRegistration(typeof(GetOrRefreshDataUserControl)).Registration;
            registration2.SuppressDiagnosticWarning(DiagnosticType.DisposableTransientComponent,
                "Reason of suppression");
            Registration registration3 = container.GetRegistration(typeof(StudyBuilderNavigatorUserControl)).Registration;
            registration3.SuppressDiagnosticWarning(DiagnosticType.DisposableTransientComponent,
                "Reason of suppression");

            container.Verify();
        }

        public T Resolve<T>() where T : class
        {
            return container.GetInstance<T>();
        }
    }
}
