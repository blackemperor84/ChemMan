# CHEM-MAN Feature Update v2.2.0

## Summary
This update implements four major feature requests from company testing:

1. **Multiple SDS files per substance** with manufacturer tracking
2. **Substance and SDS counters** per location and globally
3. **Manual CMR/SVHC flags** for mixtures
4. **Full editing** of all substance data fields

---

## Feature 1: Multiple SDS Files per Substance

### What Changed:
- **Database**: New `sds_files` table to store multiple SDS files per substance
- Each SDS file can have:
  - Original filename (displayed to user)
  - Manufacturer name (optional)
  - Upload timestamp

### User Interface:
- SDS column now displays a list of all attached SDS files
- Each file shows:
  - Clickable filename for download
  - Manufacturer name (if provided)
  - Upload timestamp
  - Delete button (✕) for authorized users
- New "+ Dodaj SDS" button to upload additional files
- Upload form includes optional "Producent" (Manufacturer) field

### How to Use:
1. Click "+ Dodaj SDS" button in the SDS column
2. Enter manufacturer name (optional)
3. Select PDF file
4. Click "Załaduj" to upload
5. Repeat to add multiple SDS files from different manufacturers

---

## Feature 2: Substance and SDS Counters

### What Changed:
- **Location View**: Shows statistics for each organizational unit:
  - 📦 Total substances in this location
  - 📄 Total SDS files in this location

- **Global View**: Shows overall statistics:
  - 📦 Total substances across all locations
  - 📄 Total SDS files across all locations

### User Interface:
- Counters displayed in a blue info box at the top of each view
- Updates automatically when substances or SDS files are added/removed

---

## Feature 3: Manual CMR/SVHC Flags for Mixtures

### What Changed:
- **Database**: Added new fields to `substances` table:
  - `contains_cmr` - for mixtures containing CMR substances
  - `contains_svhc` - for mixtures containing SVHC substances

### Existing vs New Flags:
- **For pure substances**:
  - `is_cmr` - Substance IS CMR (auto-detected or manual)
  - `is_svhc` - Substance IS SVHC (auto-detected or manual)

- **For mixtures** (NEW):
  - `contains_cmr` - Mixture CONTAINS CMR substances
  - `contains_svhc` - Mixture CONTAINS SVHC substances

### User Interface:
- Badges in the substance name column:
  - **Red badge "CMR"** - Pure substance is CMR
  - **Red badge "SVHC"** - Pure substance is SVHC
  - **Gold badge "Zaw. CMR"** - Mixture contains CMR
  - **Gold badge "Zaw. SVHC"** - Mixture contains SVHC

### How to Set:
Use the new Edit function (see Feature 4) to set these flags via checkboxes.

---

## Feature 4: Full Substance Editing

### What Changed:
- Replaced limited "Edytuj Kom." (Edit Comment) button with comprehensive "Edytuj" (Edit) button
- New modal dialog for editing ALL substance fields

### Editable Fields:
- Nazwa (Name)
- Nr CAS (CAS Number)
- Nr WE (EC Number)
- Klasyfikacja (Classification)
- Zwroty H (H-Phrases)
- SCL/ M-factor
- Lokalizacja fizyczna (Physical Location)
- Komentarz (Comment)
- **CMR/SVHC Flags** (4 checkboxes):
  - Jest CMR (substancja)
  - Jest SVHC (substancja)
  - Zawiera CMR (mieszanina)
  - Zawiera SVHC (mieszanina)

### How to Use:
1. Click "Edytuj" button in the Actions column
2. Modal dialog opens with all current values
3. Modify any fields as needed
4. Check/uncheck CMR/SVHC flags
5. Click "Zapisz" to save changes
6. Page refreshes automatically to show updates

---

## Database Migration

### Migration Script:
- File: `migrate_to_multi_sds.py`
- **Already executed successfully!**

### What the Migration Did:
1. ✅ Created `sds_files` table
2. ✅ Added `contains_cmr` column to substances
3. ✅ Added `contains_svhc` column to substances
4. ✅ Migrated 1 existing SDS file to new table

### Backwards Compatibility:
- Old `sds_filename` and `sds_upload_timestamp` fields remain in database
- These fields are still updated for compatibility
- Application now primarily uses new `sds_files` table

---

## Modified Files

### Backend (Python):
1. **models.py**
   - Added `SDSFile` model
   - Added `contains_cmr` and `contains_svhc` fields to `Substance`
   - Added relationship: `Substance.sds_files`

2. **routes/files.py**
   - Updated `upload_sds()` - supports manufacturer field
   - Updated `delete_sds()` - deletes specific SDS file by ID
   - Added `SDSFile` import

3. **routes/substances.py**
   - Added `update_substance()` - comprehensive edit endpoint
   - Handles all fields including CMR/SVHC flags

4. **routes/locations.py**
   - Updated `view_location()` - includes SDS files list
   - Added counters calculation
   - Added `SDSFile` import

5. **routes/export.py**
   - Updated `view_all_substances()` - added global counters
   - Added `SDSFile` import

### Frontend (Templates):
1. **templates/location_detail.html**
   - Updated SDS column to show multiple files
   - Added manufacturer display
   - Added "+ Dodaj SDS" button with manufacturer input
   - Added CMR/SVHC mixture badges
   - Added counters display
   - Changed "Edytuj Kom." to "Edytuj"
   - Added edit substance modal with all fields and checkboxes

2. **templates/all_substances.html**
   - Added global counters display

### Frontend (JavaScript):
1. **static/js/location_detail.js**
   - Added handlers for new "+ Dodaj SDS" button
   - Updated cancel button to show/hide correctly
   - Added complete edit substance functionality:
     - Modal opening/closing
     - Form population from table data
     - CMR/SVHC checkbox detection
     - Form submission with AJAX
     - Success/error handling

---

## Testing Checklist

### ✅ Multiple SDS Files:
- [ ] Upload first SDS file with manufacturer name
- [ ] Upload second SDS file with different manufacturer
- [ ] Verify both files are displayed with filenames
- [ ] Verify manufacturers are shown
- [ ] Download each file to confirm correct file
- [ ] Delete one SDS file
- [ ] Verify remaining file still works

### ✅ Counters:
- [ ] Check location view shows correct substance count
- [ ] Check location view shows correct SDS file count
- [ ] Add/remove substance and verify counter updates
- [ ] Add/remove SDS file and verify counter updates
- [ ] Check global view shows correct totals

### ✅ CMR/SVHC Flags:
- [ ] Edit a pure substance
- [ ] Check "Jest CMR" checkbox
- [ ] Save and verify red "CMR" badge appears
- [ ] Edit a mixture
- [ ] Check "Zawiera CMR" checkbox
- [ ] Save and verify gold "Zaw. CMR" badge appears
- [ ] Test all 4 flag combinations

### ✅ Full Editing:
- [ ] Click "Edytuj" button
- [ ] Verify all fields are populated correctly
- [ ] Modify Name field
- [ ] Modify CAS number
- [ ] Modify Classification
- [ ] Change multiple fields at once
- [ ] Toggle CMR/SVHC checkboxes
- [ ] Save and verify all changes are persisted
- [ ] Cancel edit and verify no changes saved

---

## Rollback Plan

If issues occur, you can rollback by:

1. **Restore old files** (if backups were made):
   ```bash
   # Restore from backup
   cp models.py.backup models.py
   cp routes/files.py.backup routes/files.py
   # etc.
   ```

2. **Remove new database columns** (if needed):
   ```python
   # Create rollback script
   ALTER TABLE substances DROP COLUMN contains_cmr;
   ALTER TABLE substances DROP COLUMN contains_svhc;
   DROP TABLE sds_files;
   ```

3. **Restart application**:
   ```bash
   # Stop and start Flask app
   ```

---

## Known Limitations

1. **SDS file size**: Still limited to 16MB per file (configurable)
2. **File format**: Only PDF files are supported
3. **No bulk edit**: Must edit substances one at a time
4. **Page refresh**: Full page reload after editing (not real-time)

---

## Future Enhancements

Potential improvements for next version:
- Drag-and-drop SDS file upload
- Bulk edit for multiple substances
- SDS file versioning/history
- Export counters to reports
- Real-time updates without page reload

---

## Support

If you encounter issues:
1. Check browser console for JavaScript errors
2. Check Flask logs for backend errors
3. Verify database migration completed successfully
4. Test with different browsers
5. Clear browser cache if styling looks wrong

---

**Version**: 2.2.0
**Date**: 2026-01-18
**Status**: ✅ Implementation Complete - Ready for Testing
