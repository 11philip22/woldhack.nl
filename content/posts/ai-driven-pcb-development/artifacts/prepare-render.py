"""Create a visualization copy; never save over the electrical design."""
from pathlib import Path
import pcbnew as p

dest = Path(__file__).resolve().parent
root = dest.parent.parent
source = root / 'bluepill-vbus-switch.kicad_pcb'
target = dest / 'bluepill-assembled.kicad_pcb'
target.write_text(source.read_text().replace('${KIPRJMOD}', root.as_posix()))
board = p.LoadBoard(str(target))
module = p.FOOTPRINT(board)
module.SetReference('BLUEPILL')
module.SetValue('Blue Pill - visualization only')
module.Reference().SetVisible(False)
module.Value().SetVisible(False)
module.SetPosition(p.VECTOR2I(p.FromMM(102.37), p.FromMM(99.12)))
module.SetOrientationDegrees(90)
model = p.FP_3DMODEL()
model.m_Filename = (dest / 'models/YAAJ_BluePill_PinHeaders_H_SWD_cp.wrl').as_posix()
model.m_Offset = p.VECTOR3D(0, 0, 8.5)
model.m_Scale = p.VECTOR3D(1, 1, 1)
model.m_Rotation = p.VECTOR3D(0, 0, 0)
module.Models().push_back(model)
board.Add(module)
p.SaveBoard(str(target), board)
print(target)
