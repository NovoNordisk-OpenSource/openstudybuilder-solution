using System.IO;
using System.Net.NetworkInformation;

namespace NN_Studybuilder_Protocol.Data.Services
{
    public class NetworkService
    {
        public bool IsConnectedToVpn()
        {
            if (!NetworkInterface.GetIsNetworkAvailable())
            {
                return false;
            }

            foreach (var networkInterface in NetworkInterface.GetAllNetworkInterfaces())
            {
                // First check for Cisco VPN, which NN employees must use when working remotely
                if (networkInterface.OperationalStatus == OperationalStatus.Up && networkInterface.Description.Contains("Cisco AnyConnect Secure Mobility Client Virtual Miniport Adapter"))
                {
                    return true;
                }

                // NN employees on premises automatically connect to NN network through Zscaler client
                if (networkInterface.Description.Contains("Zscaler Network Adapter"))
                {
                    // the ZScaler client does not show as OperationalStatus.Up in NetworkInterfaces, so we do a workaround by trying to access the shared Studybuilder network folder
                    var dir = @"\\FSDKHQ001\x$\NNAuthoring\StudyBuilderAddIn";
                    try
                    {
                        var dirs = Directory.GetDirectories(dir);
                    }
                    catch (IOException io)
                    {
                        if (io.Message == "The network path was not found.\r\n")
                        {
                            return false;
                        }

                        throw;
                    }

                    return true;
                }
            }

            return false;
        }
    }
}
