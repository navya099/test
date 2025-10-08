using Autodesk.Aec.Geometry;
using Autodesk.AutoCAD.DatabaseServices;
using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using System;
using System.Collections.Generic;
using System.IO.Compression;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using static System.Collections.Specialized.BitVector32;
using Profile = Autodesk.Civil.DatabaseServices.Profile;

namespace AUTO_TN_BR
{
    /// <summary>
    /// Profile 서비스 클래스
    /// </summary>
    internal class ProfileService
    {
        public ProfileService() { }

        /// <summary>
        /// Profile 얻기
        /// </summary>
        public Profile GetProfile(Alignment alignment, Transaction tr, ProfileType profileType)
        {
            foreach (ObjectId profileId in alignment.GetProfileIds())
            {
                var profile = tr.GetObject(profileId, OpenMode.ForRead) as Profile;
                if (profile != null && profile.ProfileType == profileType)
                    return profile;
            }
            return null;
        }

        /// <summary>
        /// 배치 Profile 생성
        /// </summary>
        internal Profile CreateLayoutProfile(ObjectId alignmentId, Alignment alignment, string profileName, CivilDocument civildoc, Transaction tr)
        {
            // 1️ 스타일 가져오기
            ObjectId profileStyleId = civildoc.Styles.ProfileStyles[0];
            ObjectId profileLabelSetId = civildoc.Styles.LabelSetStyles.ProfileLabelSetStyles[0];

            // 2️ Profile 생성 -> ObjectId 반환
            ObjectId profileId = Profile.CreateByLayout(profileName, alignmentId, alignment.LayerId, profileStyleId, profileLabelSetId);

            // 3️ Transaction 내에서 Profile 객체 가져오기
            Profile? profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;

            // 4️⃣ 반환
            return profile;
        }
        /// <summary>
        /// 지표면 Profile 생성
        /// </summary>
        internal Profile CreateSurfaceProfile(ObjectId alignmentId, Alignment alignment, string profileName, ObjectId surfaceid, CivilDocument civildoc, Transaction tr)

        {
            // 1️ 스타일 가져오기
            ObjectId profileStyleId = civildoc.Styles.ProfileStyles[0];
            ObjectId profileLabelSetId = civildoc.Styles.LabelSetStyles.ProfileLabelSetStyles[0];

            // 2️ Profile 생성 -> ObjectId 반환
            ObjectId profileId = Profile.CreateFromSurface(profileName, alignmentId, surfaceid, alignment.LayerId, profileStyleId, profileLabelSetId);

            // 3️ Transaction 내에서 Profile 객체 가져오기
            Profile? profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;

            // 4️⃣ 반환
            return profile;
        }

        /// <summary>
        /// 지정된 profilename Profile 객체를 제거
        /// </summary>
        internal void RemoveProfile(Alignment baseAlignment, string profilename, Transaction tr)
        {
            // Alignment의 모든 Profile 중 이름이 같은 것 찾기
            foreach (ObjectId profileId in baseAlignment.GetProfileIds())
            {
                Profile? profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;
                if (profile != null && profile.Name == "지반선")
                {
                    // Alignment 컬렉션에서 제거
                    
                    profile.Erase(true);// 트랜잭션 내에서 삭제
                    Logger.Instance.SetMessage($"기존 종단 삭제 완료");
                    profile = null;
                    break;
                }
            }
        }
        /// <summary>
        /// 지정된 profilename Profile가 중복되는지 확인
        /// </summary>
        internal bool IsDuplicateProfile(Alignment baseAlignment, string profilename, Transaction tr)
        {
            bool result = false;
            // Alignment의 모든 Profile 중 이름이 같은 것 찾기
            foreach (ObjectId profileId in baseAlignment.GetProfileIds())
            {
                Profile? profile = tr.GetObject(profileId, OpenMode.ForRead) as Profile;
                if (profile != null && profile.Name == "지반선")
                {
                    result = true;
                    break;
                }
            }
            return result;
        }

        /// <summary>
        /// Profile내 표고 추출
        /// </summary>
        internal double GetElevationByStation(double station, Profile profile)
        {
            double elevation = profile.ElevationAt(station);
            return elevation;
        }

        /// <summary>
        /// Profile내 표고 추출 리스트
        /// </summary>
        internal List<double> GetElevationByStation(List<double> stations, Profile profile)
        {
            return stations.Select(sta => GetElevationByStation(sta, profile)).ToList();
        }

        /// <summary>
        /// 표고차 계산
        /// </summary>
        internal double GetElevationDifference(double firstElevation, double secondElevation)
        {
            return firstElevation - secondElevation;
        }

        /// <summary>
        /// 표고차 계산 리스트
        /// </summary>
        internal List<double> GetElevationDifference(List<double> firstElevations, List<double> secondElevations)
        {
            if (firstElevations.Count != secondElevations.Count)
                throw new ArgumentException("두 리스트의 길이가 같아야 합니다.");

            return firstElevations
                .Select((f, i) => GetElevationDifference(f, secondElevations[i]))
                .ToList();
        }



    }
}
