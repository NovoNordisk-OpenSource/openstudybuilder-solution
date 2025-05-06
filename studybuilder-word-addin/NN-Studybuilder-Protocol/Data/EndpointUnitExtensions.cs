using System;

namespace NN_Studybuilder_Protocol.Data
{
    public static class EndpointUnitExtensions
    {
        public static string Format(this EndpointUnitDto endpointUnitDto)
        {
            if (endpointUnitDto == null) return string.Empty;
            if (endpointUnitDto.Units == null) return string.Empty;
            if (!string.IsNullOrWhiteSpace(endpointUnitDto.Separator))
                return string.Join($" {endpointUnitDto.Separator} ", endpointUnitDto.Units);

            if (endpointUnitDto.Units.Length == 1)
                return endpointUnitDto.Units[0];

            //throw new Exception("Invalid Endpoint Unit data received");
            return string.Empty;
        }
    }
}
