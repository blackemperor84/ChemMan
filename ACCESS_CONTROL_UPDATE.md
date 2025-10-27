# Update: Revised Access Control for Organizational Units

## Date: 2025-10-27
## Version: 1.2.0

## Summary of Changes

Based on user feedback, the access control model has been updated to be more flexible:

### Previous Model (v1.1.0)
- Users could ONLY see their assigned organizational unit
- Users could ONLY modify their assigned unit
- Very restrictive - prevented viewing other departments

### New Model (v1.2.0)
- Users can VIEW all organizational units (read-only access)
- Users can MODIFY only their assigned organizational unit
- Users can COPY/MOVE substances from other units ONLY TO their own unit (not to other units)

## Changes Made

### 1. Navigation Link Updated
**File:** `templates/base.html`
- Changed "Lista Lokalizacji" → "Komórki Organizacyjne"

### 2. User Model - New Access Methods
**File:** `models.py`

**Updated method:**
```python
def has_access_to_organizational_unit(self, location_id: int) -> bool:
    """
    Checks if user can VIEW an organizational unit.
    - Admin: access to all units
    - Regular users: can view ALL units (read-only)
    - Users without assignment: no access
    """
```

**New method:**
```python
def can_modify_organizational_unit(self, location_id: int) -> bool:
    """
    Checks if user can MODIFY an organizational unit.
    - Admin: can modify all units
    - Regular users: can modify ONLY their assigned unit
    """
```

### 3. Routes Updated

#### Location Routes (`routes/locations.py`)

**`index()`**
- Now shows ALL organizational units to users with assignment
- Previously showed only assigned unit

**`view_location(location_id)`**
- Added `can_modify` flag passed to template
- Determines if user can edit this specific unit
- `other_locations` filtering updated:
  - Admin: sees all other units
  - Regular user viewing other unit: sees only their assigned unit (as copy target)
  - Regular user viewing own unit: sees empty list (can't copy to self)

**`update_location_name(location_id)`**
- Changed from `has_access_to_organizational_unit()` to `can_modify_organizational_unit()`
- Error message: "Możesz edytować tylko substancje w swojej komórce organizacyjnej."

**`delete_location(location_id)`**
- Changed from `has_access_to_organizational_unit()` to `can_modify_organizational_unit()`
- Error message: "Możesz usuwać tylko komórki organizacyjne przypisane do Ciebie."

#### Substance Routes (`routes/substances.py`)

All substance modification routes now use `can_modify_organizational_unit()`:
- `add_substance_to_location()` - "Możesz dodawać substancje tylko do swojej komórki organizacyjnej."
- `add_manual_substance()` - "Możesz dodawać substancje tylko do swojej komórki organizacyjnej."
- `delete_substance()` - "Możesz usuwać substancje tylko z swojej komórki organizacyjnej."
- `update_substance_comment()` - "Możesz edytować substancje tylko w swojej komórce organizacyjnej."
- `move_substances()` - "Możesz przenosić substancje tylko do swojej komórki organizacyjnej."
- `copy_substances()` - "Możesz kopiować substancje tylko do swojej komórki organizacyjnej."

**Key change:** Target location validation added to ensure users can only copy/move TO their assigned unit.

### 4. Templates Updated

#### `location_detail.html`

**Data attributes updated:**
```html
data-can-add="{{ (can_modify_this_unit and (current_user.is_admin or current_user.can_add))|lower }}"
data-can-edit="{{ (can_modify_this_unit and (current_user.is_admin or current_user.can_edit))|lower }}"
data-can-delete="{{ (can_modify_this_unit and (current_user.is_admin or current_user.can_delete))|lower }}"
data-can-upload-sds="{{ (can_modify_this_unit and (current_user.is_admin or current_user.can_upload_sds))|lower }}"
```

**Move/Copy remain available:**
```html
data-can-move="{{ (current_user.is_admin or current_user.can_move)|lower }}"
data-can-copy="{{ (current_user.is_admin or current_user.can_copy)|lower }}"
```

**Edit/Delete buttons conditional:**
- Only shown when `can_modify_this_unit` is True
- SDS upload/change/delete only when `can_modify_this_unit` is True
- Add sections only shown when `can_modify_this_unit` is True

#### `locations.html`

**Edit/Delete buttons conditional:**
```html
{% if current_user.can_modify_organizational_unit(location.id) and (current_user.is_admin or current_user.can_edit) %}
    <button class="edit-location-btn">Edytuj</button>
{% endif %}
```

## User Experience

### Scenario: User assigned to "Laboratorium SLK."

#### What user CAN do:
✅ View "Laboratorium SLK." unit
✅ View "RBR-K" unit (read-only)
✅ View all substances in both units
✅ Add substances to "Laboratorium SLK."
✅ Edit substances in "Laboratorium SLK."
✅ Delete substances from "Laboratorium SLK."
✅ Copy substances FROM "RBR-K" TO "Laboratorium SLK."
✅ Upload/modify SDS in "Laboratorium SLK."

#### What user CANNOT do:
❌ Add substances to "RBR-K"
❌ Edit substances in "RBR-K"
❌ Delete substances from "RBR-K"
❌ Upload/modify SDS in "RBR-K"
❌ Edit "RBR-K" unit name
❌ Delete "RBR-K" unit
❌ Copy substances FROM "RBR-K" TO any unit other than "Laboratorium SLK."
❌ Copy substances FROM "Laboratorium SLK." TO "RBR-K"

## Testing Instructions

### Test 1: Viewing Access

1. Create user `lab_user` assigned to "Laboratorium SLK." (ID: 1)
2. Login as `lab_user`
3. **Expected:** See both "Laboratorium SLK." and "RBR-K" in list
4. Click on "RBR-K"
5. **Expected:** Can view substances, but NO edit/delete/add buttons shown

### Test 2: Modification Access

1. While logged in as `lab_user`
2. Go to "Laboratorium SLK."
3. **Expected:** Edit/Delete/Add buttons ARE shown
4. Try to add a substance
5. **Expected:** Works successfully

### Test 3: Copying Between Units

1. While logged in as `lab_user` viewing "RBR-K"
2. Select a substance
3. Check the copy dropdown
4. **Expected:** Dropdown shows ONLY "Laboratorium SLK." (user's assigned unit)
5. Copy substance to "Laboratorium SLK."
6. **Expected:** Copy succeeds

**Test 3b: Verify restriction**
1. While logged in as `lab_user` viewing "Laboratorium SLK."
2. **Expected:** Copy dropdown is empty or hidden (can't copy to same unit)
3. Try to copy via API to "RBR-K" (ID: 2)
4. **Expected:** HTTP 403 error "Możesz kopiować substancje tylko do swojej komórki organizacyjnej."

### Test 4: Direct URL Access (Security)

1. While logged in as `lab_user`
2. Try to directly POST to: `/location/2/add_substance` (RBR-K)
3. **Expected:** HTTP 403 Forbidden error
4. Message: "Możesz dodawać substancje tylko do swojej komórki organizacyjnej."

### Test 5: UI Consistency

1. Login as `lab_user`
2. Navigate to "RBR-K"
3. **Expected UI elements:**
   - ✅ Can see substance list
   - ✅ Can view SDS files (download links)
   - ✅ Can see copy/move controls
   - ❌ NO "Edytuj Kom." buttons
   - ❌ NO "Usuń" buttons
   - ❌ NO "Dodaj" section at bottom
   - ❌ NO SDS upload buttons
   - ❌ NO edit/delete location buttons in list

## Admin Behavior

Administrators are NOT affected by these restrictions:
- Can view ALL units
- Can modify ALL units
- Can add/edit/delete in ALL units

## Database Schema

No changes to database schema - uses existing `organizational_unit_id` column.

## Files Modified

1. `templates/base.html` - Navigation link text
2. `models.py` - Access control methods
3. `routes/locations.py` - View-all access, modify restrictions
4. `routes/substances.py` - Modification restrictions
5. `templates/location_detail.html` - Conditional edit controls
6. `templates/locations.html` - Conditional edit/delete buttons

## Rollback Instructions

If needed to rollback to previous restrictive model:

1. In `models.py` `has_access_to_organizational_unit()`:
   ```python
   # Change this line:
   if self.organizational_unit_id is not None:
       return True

   # Back to:
   return self.organizational_unit_id == location_id
   ```

2. In `routes/locations.py` `index()`:
   ```python
   # Change back to:
   elif current_user.organizational_unit_id:
       locations = Location.query.filter_by(id=current_user.organizational_unit_id).all()
   ```

## Security Notes

✅ Backend routes enforce modification restrictions
✅ Templates hide UI elements but DON'T rely on them for security
✅ Direct API access is blocked by route-level checks
✅ All modification operations validate `can_modify_organizational_unit()`

## Support

For questions or issues:
- Check TESTING_GUIDE.md for detailed testing procedures
- Check ORGANIZATIONAL_UNITS_UPDATE.md for original implementation details

---
**Author:** Claude Code
**Review Status:** Ready for Testing
