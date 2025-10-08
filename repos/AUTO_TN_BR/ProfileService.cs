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
            Profile profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;

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
            Profile profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;

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
                Profile profile = tr.GetObject(profileId, OpenMode.ForWrite) as Profile;
                if (profile != null && profile.Name == "지반선")
                {
                    profile.Erase();// 트랜잭션 내에서 삭제
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
                Profile profile = tr.GetObject(profileId, OpenMode.ForRead) as Profile;
                if (profile != null && profile.Name == "지반선")
                {
                    result = true;
                    break;
                }
            }
            return result;
        }
    }
}
