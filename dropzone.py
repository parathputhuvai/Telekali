import os
import zipfile
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import DROPZONE_LIMIT_MB, DROPZONE_WARN_MB, AUTHORIZED_USER_ID

# Define Drop Zone Path: ~/TeleKali/dropzone
DROPZONE_DIR = Path.home() / "TeleKali" / "dropzone"
DROPZONE_DIR.mkdir(parents=True, exist_ok=True)


def get_dir_size_mb(directory: Path) -> float:
    """Calculate total size of the directory in MB."""
    total_size = sum(f.stat().st_size for f in directory.glob('**/*') if f.is_file())
    return total_size / (1024 * 1024)


def get_unique_filename(base_name: str) -> Path:
    """Auto-increments filename to prevent overwrites (e.g., payload(1).py)."""
    target_path = DROPZONE_DIR / base_name
    if not target_path.exists():
        return target_path
    
    name = target_path.stem
    ext = target_path.suffix
    counter = 1
    while True:
        new_path = DROPZONE_DIR / f"{name}({counter}){ext}"
        if not new_path.exists():
            return new_path
        counter += 1


async def handle_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Silently catches documents and photos, generating a storage receipt."""
    message = update.effective_message
    
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name or "uploaded_document"
        file_size = message.document.file_size
    elif message.photo:
        photo = message.photo[-1]  # Get highest resolution
        file_id = photo.file_id
        file_name = f"photo_{message.message_id}.jpg"
        file_size = photo.file_size
    else:
        return

    target_path = get_unique_filename(file_name)
    
    # Download file to Kali
    new_file = await context.bot.get_file(file_id)
    await new_file.download_to_drive(custom_path=target_path)
    
    # Generate Receipt
    current_size_mb = get_dir_size_mb(DROPZONE_DIR)
    file_size_mb = (file_size / (1024 * 1024)) if file_size else 0
    
    warning = ""
    if current_size_mb >= DROPZONE_WARN_MB:
        warning = "\n⚠️ WARNING: Storage threshold reached!"
        
    receipt = (
        f"✅ Saved: {target_path.name} ({file_size_mb:.2f} MB)\n"
        f"Dropzone: {current_size_mb:.2f}MB / {DROPZONE_LIMIT_MB}MB used.{warning}"
    )
    await message.reply_text(receipt)


async def list_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sends interactive UI menu sorted by newest files first."""
    user = update.effective_user
    if user is None or user.id != AUTHORIZED_USER_ID:
        return

    files = [f for f in DROPZONE_DIR.iterdir() if f.is_file()]
    
    if not files:
        await update.effective_message.reply_text("📂 Dropzone is currently empty.")
        return

    # Sort by Modified Time (Newest First)
    files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
    
    keyboard = []
    for f in files:
        size_mb = f.stat().st_size / (1024 * 1024)
        # Using dl| prefix to identify download callbacks
        callback_data = f"dl|{f.name}"
        # Telegram restricts callback data to 64 bytes, truncate if necessary
        if len(callback_data.encode('utf-8')) > 64:
            continue 
            
        keyboard.append([InlineKeyboardButton(f"📄 {f.name} ({size_mb:.1f}MB)", callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.effective_message.reply_text("📁 Dropzone Files:", reply_markup=reply_markup)


async def handle_download_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes button clicks, applying compression and burn-after-reading UX."""
    user = update.effective_user
    if user is None or user.id != AUTHORIZED_USER_ID:
        return

    query = update.callback_query
    await query.answer()
    
    data = query.data
    if not data.startswith("dl|"):
        return
        
    raw_filename = data.split("|", 1)[1]
    filename = Path(raw_filename).name
    target_path = DROPZONE_DIR / filename
    
    if (
        not filename
        or not target_path.is_file()
        or target_path.resolve().parent != DROPZONE_DIR.resolve()
    ):
        await query.edit_message_text(f"❌ File no longer exists: {filename}")
        return
        
    file_size_mb = target_path.stat().st_size / (1024 * 1024)
    send_path = target_path

    # Auto-Compress if over Telegram's 50MB limit
    if file_size_mb > 49.5:
        status_msg = await query.message.reply_text(f"⏳ {filename} exceeds 50MB. Compressing now...")
        zip_path = target_path.with_suffix('.zip')
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(target_path, target_path.name)
        
        send_path = zip_path
        await status_msg.delete()
        
        if (send_path.stat().st_size / (1024 * 1024)) > 49.5:
            await query.message.reply_text("❌ File still exceeds 50MB after compression. Download aborted.")
            if send_path != target_path:
                send_path.unlink()
            return

    # Burn After Reading
    await query.edit_message_text(f"✅ Downloaded: {filename}")
    
    with open(send_path, 'rb') as doc:
        await context.bot.send_document(chat_id=query.message.chat_id, document=doc)
        
    # Cleanup temporary zip if one was created
    if send_path != target_path:
        send_path.unlink()