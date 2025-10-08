using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using Autodesk.AutoCAD.DatabaseServices;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AUTO_TN_BR
{
    internal class ProfileBuilder
    {
        private readonly ProfileService _profileService = new();
        private readonly SurfaceService _surfaceService = new();

        public ProfileBuilder() { }
        /// <summary>
        /// 종단 빌드 수행 메서드(추가, 삭제, 수정)
        /// </summary>
        public Profile CreateSurfaceProfile(Transaction tr, CivilDocument doc, Alignment baseAlignment,
                                             List<double> stations, List<double> elevations)
        {
            var profileProvider = new ProfileService();
            string profileName = "지반선";

            // 기존 Profile 삭제
            if (profileProvider.IsDuplicateProfile(baseAlignment, profileName, tr))
                profileProvider.RemoveProfile(baseAlignment, profileName, tr);

            // Surface 생성 / 중복 처리
            var surfaceProvider = new SurfaceService();
            string surfaceName = "Surface1";
            ObjectId surfaceId = ObjectId.Null;

            if (surfaceProvider.HasAnyTinSurface(doc))
            {
                if (surfaceProvider.IsDuplicateTinSurface(surfaceName, doc, tr))
                {
                    surfaceProvider.RemoveTinSurface(surfaceName, doc, tr);
                    surfaceProvider.CreateTinSurface(surfaceName, doc, ref surfaceId);
                }
            }
            else
            {
                surfaceProvider.CreateTinSurface(surfaceName, doc, ref surfaceId);
            }

            // Profile 생성
            Profile profile = profileProvider.CreateSurfaceProfile(baseAlignment.ObjectId, baseAlignment,
                                                                  profileName, surfaceId, doc, tr);

            // PVI 추가
            foreach (var pair in stations.Zip(elevations, (station, elev) => (station, elev)))
                profile.PVIs.AddPVI(pair.station, pair.elev);

            return profile;
        }
    }
}
