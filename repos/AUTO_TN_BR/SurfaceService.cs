using Autodesk.Civil.ApplicationServices;
using Autodesk.Civil.DatabaseServices;
using Autodesk.AutoCAD.DatabaseServices;
using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using CivSurface = Autodesk.Civil.DatabaseServices.Surface;

namespace AUTO_TN_BR
{
    internal class SurfaceService
    {
        public SurfaceService() { }

        /// <summary>
        /// 빈 TIN Surface 생성 
        /// </summary> 
        internal TinSurface CreateTinSurface(string surfaceName, CivilDocument civildoc, ref ObjectId surfaceid)
        { 
            ObjectId surfaceStyleId = civildoc.Styles.SurfaceStyles[3];
            surfaceid = TinSurface.Create(surfaceName, surfaceStyleId); 
            TinSurface surface = surfaceid.GetObject(OpenMode.ForRead) as TinSurface; 
            return surface; 
        }
        
        /// <summary>
        /// 모든 TIN Surface를 반환
        /// </summary>
        private IEnumerable<TinSurface> GetAllTinSurfaces(CivilDocument civildoc, Transaction tr)
        {
            foreach (ObjectId id in civildoc.GetSurfaceIds())
            {
                if (tr.GetObject(id, OpenMode.ForRead) is TinSurface surface)
                    yield return surface;
            }
        }

        /// <summary>
        /// 지표면이 하나라도 존재하는지 확인
        /// </summary>
        internal bool HasAnyTinSurface(CivilDocument civildoc)
        {
            return civildoc.GetSurfaceIds().Count > 0;
        }

        /// <summary>
        /// 지정된 이름의 Surface가 존재하는지 확인
        /// </summary>
        internal bool IsDuplicateTinSurface(string surfaceName, CivilDocument civildoc, Transaction tr)
        {
            return GetAllTinSurfaces(civildoc, tr)
                .Any(s => s.Name.Equals(surfaceName, StringComparison.OrdinalIgnoreCase));
        }

        /// <summary>
        /// 지정된 이름의 Surface 제거
        /// </summary>
        internal void RemoveTinSurface(string surfaceName, CivilDocument civildoc, Transaction tr)
        {
            foreach (var surface in GetAllTinSurfaces(civildoc, tr))
            {
                if (surface.Name.Equals(surfaceName, StringComparison.OrdinalIgnoreCase))
                {
                    surface.UpgradeOpen(); // 삭제 전 ForWrite 모드로 전환
                    surface.Erase();
                    Logger.Instance.SetMessage($"기존 지표면 '{surfaceName}' 제거 완료");
                    break;
                }
            }
        }

    }
}
