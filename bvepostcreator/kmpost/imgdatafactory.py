from model.bveimgdata import BVEImageData


class KMImageDataFactory:
    def create(self, post_type, station, structure):
        km_int = round(station * 0.001, 1)
        km, m = f"{km_int:.1f}".split('.')

        return BVEImageData(
            km_string=km,
            m_string=m,
            imgname=str(station),
            img_bg_color=(2, 6, 140),
            txt_color=(255, 255, 255),
            openfile_name=f'{post_type}_{structure}용'
        )
