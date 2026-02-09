from model.equipment import EquipmentDTO


class TkEquipmentAdapter:
    @staticmethod
    def collect(tk_vms: list):
        dtos = []
        for i, vm in enumerate(tk_vms):
            dtos.append(
                EquipmentDTO(
                    name=vm.name_var.get(),
                    xoffset=vm.x_var.get(),
                    yoffset=vm.y_var.get(),
                    rotation=vm.rotation_var.get(),
                    base_rail_index=vm.base_rail_index_var.get(),
                )
            )
        return dtos
