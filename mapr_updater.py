"""
MAPR Updater - Update Memory and Progress Report (MAPR)
Usage: python mapr_updater.py [command] [options]

Commands:
  add-done    - Tambah item yang sudah selesai
  add-pending - Tambah item yang belum selesai  
  add-note    - Tambah catatan sesi
  status      - Tampilkan status ringkasan
  export      - Export MAPR ke format lain
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

MAPR_FILE = Path(__file__).parent / "MEMORY_AND_PROGRESS_REPORT.md"

TEMPLATE_SECTION = """
## 📝 Catatan Terbaru

- **Tanggal:** {date}
- **Item:** {item}
- **Status:** {status}
- **Notes:** {notes}

---

"""

class MAPRUpdater:
    def __init__(self):
        self.mapr_path = MAPR_FILE
        self.content = self._read_file()
    
    def _read_file(self):
        if self.mapr_path.exists():
            return self.mapr_path.read_text(encoding='utf-8')
        return ""
    
    def _write_file(self, content):
        self.mapr_path.write_text(content, encoding='utf-8')
        print(f"✅ MAPR updated: {self.mapr_path}")
    
    def add_done(self, item, notes=""):
        """Tambah item yang sudah selesai"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"- ✅ **{item}** - Selesai ({timestamp})"
        if notes:
            entry += f" | Catatan: {notes}"
        
        return self._add_entry_to_section("## ✅ YANG SUDAH SELESAI", entry)
    
    def add_pending(self, item, notes=""):
        """Tambah item yang belum selesai"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        entry = f"- ⏳ **{item}** - Belum selesai"
        if notes:
            entry += f" | Target: {notes}"
        
        return self._add_entry_to_section("## ⏳ YANG BELUM/ONGOING", entry)
    
    def _add_entry_to_section(self, section_header, new_entry):
        if section_header not in self.content:
            print(f"⚠️ Section '{section_header}' tidak ditemukan")
            return False
        
        lines = self.content.split('\n')
        section_idx = None
        insert_idx = None
        
        for i, line in enumerate(lines):
            if line.strip() == section_header:
                section_idx = i
                for j in range(i+1, len(lines)):
                    if lines[j].strip().startswith('## '):
                        insert_idx = j
                        break
                if insert_idx is None:
                    insert_idx = len(lines)
                break
        
        if insert_idx:
            lines.insert(insert_idx, new_entry)
            self.content = '\n'.join(lines)
            self._write_file(self.content)
            return True
        return False
    
    def add_note(self, title, content):
        """Tambah catatan sesi baru"""
        note_section = f"""
### 📌 {title}
**Tanggal:** {datetime.now().strftime("%Y-%m-%d %H:%M")}
{content}
"""
        return self._add_entry_before_footer(note_section)
    
    def _add_entry_before_footer(self, entry):
        footer = "---"
        if footer in self.content:
            idx = self.content.index(footer)
            self.content = self.content[:idx] + entry + "\n" + self.content[idx:]
            self._write_file(self.content)
            return True
        return False
    
    def update_next_steps(self, item, status="pending"):
        """Update next steps section"""
        pattern = r'### 7\.1 Priority Items\s*\n(.*?)(?=\n###|\n---)'
        
        def replacement(match):
            current = match.group(1)
            if status == "done":
                new_item = f"- ~~{item}~~ ✅"
            else:
                new_item = f"- [ ] {item}"
            return f"### 7.1 Priority Items\n{current}\n  {new_item}"
        
        self.content = re.sub(pattern, replacement, self.content, flags=re.DOTALL)
        self._write_file(self.content)
    
    def show_status(self):
        """Tampilkan status ringkasan"""
        done_count = len(re.findall(r'^- ✅', self.content, re.MULTILINE))
        pending_count = len(re.findall(r'^- ⏳', self.content, re.MULTILINE))
        
        print("=" * 40)
        print("📊 MAPR Status Summary")
        print("=" * 40)
        print(f"✅ Selesai: {done_count}")
        print(f"⏳ Pending: {pending_count}")
        print(f"📁 File: {self.mapr_path}")
        print("=" * 40)
        
        print("\n📋 Item yang sudah selesai:")
        for match in re.finditer(r'^- ✅ \*\*(.*?)\*\*', self.content):
            print(f"  • {match.group(1)}")
        
        print("\n📋 Item yang belum:")
        for match in re.finditer(r'^- ⏳ \*\*(.*?)\*\*', self.content):
            print(f"  • {match.group(1)}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='MAPR Updater')
    parser.add_argument('command', choices=['add-done', 'add-pending', 'add-note', 'status'],
                       help='Command to execute')
    parser.add_argument('--item', '-i', help='Item description')
    parser.add_argument('--notes', '-n', help='Additional notes')
    parser.add_argument('--title', '-t', help='Title for notes')
    parser.add_argument('--content', '-c', help='Content for notes')
    
    args = parser.parse_args()
    
    updater = MAPRUpdater()
    
    if args.command == 'add-done':
        if not args.item:
            print("❌ Gunakan --item untuk menentukan item")
            return
        updater.add_done(args.item, args.notes or "")
    
    elif args.command == 'add-pending':
        if not args.item:
            print("❌ Gunakan --item untuk menentukan item")
            return
        updater.add_pending(args.item, args.notes or "")
    
    elif args.command == 'add-note':
        if not args.title or not args.content:
            print("❌ Gunakan --title dan --content untuk catatan")
            return
        updater.add_note(args.title, args.content)
    
    elif args.command == 'status':
        updater.show_status()


if __name__ == "__main__":
    main()