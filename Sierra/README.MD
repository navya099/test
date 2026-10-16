# Project Sierra

**Project Sierra** is a PyQt-based graphical editor for designing and analyzing railway longitudinal profiles.  
It allows engineers to interactively place, move, and delete VIP points, visualize ground profiles, and manage gradient calculations in real time.

---

## ✨ Features
- **Ground Profile Visualization**  
  Load elevation data from TXT files and display the ground line in blue.

- **Interactive VIP Points**  
  - Add VIP points by clicking on empty space.  
  - Drag points to adjust their position.  
  - Delete points with right-click.  
  - Points are automatically connected with a red plan line.

- **Dynamic Table UI**  
  - Displays VIP information in real time.  
  - Columns: `구분, STA, EL, 진입구배, 진출구배, 구배변화량`.  
  - Rows: BP, VIP1, VIP2, …, EP.  
  - Editing STA/EL in the table updates the graph instantly.

- **Future Integration**  
  - Planned connection with `_calculate_once()` engine for gradient checks.  
  - Automatic computation of entry/exit gradients and gradient change values.

---

## 🛠️ Installation
```bash
git clone https://github.com/your-repo/project-sierra.git
cd project-sierra
pip install -r requirements.txt
