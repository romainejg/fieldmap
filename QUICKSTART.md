# Quick Start Guide

## Installation & Setup

1. **Install Python** (3.8 or higher)

2. **Clone the repository:**
   ```bash
   git clone https://github.com/romainejg/fieldmap.git
   cd fieldmap
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   streamlit run app.py
   ```

## For Mobile Access

To access from a mobile device on the same network:

```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

Then access from your mobile browser using: `http://YOUR_COMPUTER_IP:8501`

## Basic Workflow

1. **Create a Session** - Open sidebar → Create New Session
2. **Take Photos** - Camera tab → Take photo → Add comment → Save
3. **View & Annotate** - Gallery tab → Select photo → Add annotations
4. **Export Data** - Sidebar → Export to Excel → Download

## Tips

- Keep your phone in portrait mode for best experience
- Export data regularly (data is session-based, not permanently stored)
- Grant camera permissions when prompted
- Use descriptive session names (e.g., "Procedure_2024_12_13")

## Features at a Glance

✅ Mobile-optimized interface
✅ Direct camera integration
✅ Session-based organization
✅ Photo annotations with timestamps
✅ Excel export for data analysis
✅ Move photos between sessions
✅ Edit comments and annotations
