# Testing Guide - Organizational Units Feature

## Current Database State

**Users:**
- admin (ID: 2) - No organizational unit assigned (has access to all units)

**Organizational Units:**
- Laboratorium SLK. (ID: 1)
- RBR-K (ID: 2)

## Step-by-Step Testing

### 1. Start the Application

```bash
cd "C:\Users\HP\Desktop\chem-man app"
flask run
```

### 2. Test Admin Access

1. **Login as admin**
   - Go to: http://127.0.0.1:5000/login
   - Login with admin credentials

2. **Verify admin sees all organizational units**
   - Go to homepage: http://127.0.0.1:5000/
   - You should see BOTH organizational units:
     - ✓ Laboratorium SLK.
     - ✓ RBR-K

3. **Check terminology changes**
   - Page header should say: "KOMÓRKI ORGANIZACYJNE" (not "LOKALIZACJE")
   - Button should say: "Dodaj Komórkę Organizacyjną" (not "Dodaj Lokalizację")

### 3. Create Test Users

1. **Go to User Management**
   - Navigate to: http://127.0.0.1:5000/admin/users

2. **Create User 1 (Laboratorium user)**
   - Username: `lab_user`
   - Password: `testpass123`
   - Organizational unit: Select "Laboratorium SLK."
   - Permissions: Check "Przeglądanie", "Dodawanie", "Edycja"
   - Click "Dodaj użytkownika"

3. **Create User 2 (RBR-K user)**
   - Username: `rbr_user`
   - Password: `testpass123`
   - Organizational unit: Select "RBR-K"
   - Permissions: Check "Przeglądanie", "Dodawanie", "Edycja"
   - Click "Dodaj użytkownika"

4. **Create User 3 (No assignment)**
   - Username: `no_unit_user`
   - Password: `testpass123`
   - Organizational unit: Leave as "Brak przypisania"
   - Permissions: Check "Przeglądanie"
   - Click "Dodaj użytkownika"

### 4. Test Access Control

#### Test 1: User with Laboratorium Access

1. **Logout and login as `lab_user`**

2. **Check homepage**
   - Should see BOTH "Laboratorium SLK." AND "RBR-K"
   - Both should be clickable

3. **Access Laboratorium (your assigned unit)**
   - Click on "Laboratorium SLK."
   - Should see: Edit buttons, Delete buttons, Add section at bottom
   - Can add/edit/delete substances

4. **Access RBR-K (other unit - read-only)**
   - Click on "RBR-K"
   - Should see substances list
   - Should NOT see: Edit buttons, Delete buttons, Add section
   - Can view substances and download SDS files
   - Check copy dropdown: Should show ONLY "Laboratorium SLK." as target
   - Can copy substances FROM RBR-K TO "Laboratorium SLK."

5. **Try to modify RBR-K via API** (security test)
   - While viewing RBR-K, try using browser console:
   ```javascript
   fetch('/location/2/add_substance', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({name: 'Test', cas: '123'})
   })
   ```
   - Should receive HTTP 403 error
   - Message: "Możesz dodawać substancje tylko do swojej komórki organizacyjnej."

#### Test 2: User with RBR-K Access

1. **Logout and login as `rbr_user`**

2. **Check homepage**
   - Should see BOTH "RBR-K" AND "Laboratorium SLK."
   - Both should be clickable

3. **Access RBR-K (your assigned unit)**
   - Click on "RBR-K"
   - Should see: Edit buttons, Delete buttons, Add section at bottom
   - Can add/edit/delete substances

4. **Access Laboratorium (other unit - read-only)**
   - Click on "Laboratorium SLK."
   - Should see substances list
   - Should NOT see: Edit buttons, Delete buttons, Add section
   - Can view substances and download SDS files
   - Can copy substances from Lab to your own unit (RBR-K)

5. **Try to modify Laboratorium via API** (security test)
   - Should receive HTTP 403 error with appropriate message

#### Test 3: User without Assignment

1. **Logout and login as `no_unit_user`**

2. **Check homepage**
   - Should see NO organizational units
   - Should see warning: "Nie masz przypisanej komórki organizacyjnej. Skontaktuj się z administratorem."

3. **Try to access any unit directly**
   - Should be blocked with error message

### 5. Test Admin Features

1. **Login as admin**

2. **Edit user assignments**
   - Go to: http://127.0.0.1:5000/admin/users
   - Click "Edytuj uprawnienia" for `lab_user`
   - Change organizational unit to "RBR-K"
   - Click "Zapisz"
   - Verify the change is shown in the user list

3. **Check terminology in all pages**
   - User management page should show "Komórka: [name]" for each user
   - Forms should have "Komórka organizacyjna" dropdown

## Expected Results Summary

| User | Can See | Can View Lab | Can Modify Lab | Can View RBR-K | Can Modify RBR-K |
|------|---------|-------------|----------------|---------------|------------------|
| admin | Both units | ✓ Yes | ✓ Yes | ✓ Yes | ✓ Yes |
| lab_user (assigned to Lab) | Both units | ✓ Yes | ✓ Yes | ✓ Yes (read-only) | ✗ No |
| rbr_user (assigned to RBR-K) | Both units | ✓ Yes (read-only) | ✗ No | ✓ Yes | ✓ Yes |
| no_unit_user (no assignment) | None | ✗ No | ✗ No | ✗ No | ✗ No |

## Security Tests

### Test 1: Direct URL Access for Viewing
- User assigned to Lab tries: http://127.0.0.1:5000/location/2 (RBR-K)
- Expected: PAGE LOADS successfully (read-only view)
- UI should NOT show edit/delete/add controls

### Test 2: API Endpoint Access
Try to add substance to unauthorized unit via API (if using fetch/AJAX):
```javascript
fetch('/location/2/add_substance', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({name: 'Test', cas: '123-45-6'})
})
```
- Expected: HTTP 403 Forbidden

### Test 3: Copy Between Units - Restricted to Assigned Unit
- Lab user viewing RBR-K can copy substances to Laboratorium ONLY
- Expected: Copy dropdown shows ONLY "Laboratorium SLK." (user's assigned unit)
- Expected: Copy operation succeeds
- Lab user viewing Laboratorium sees empty dropdown (can't copy to same unit)
- Lab user CANNOT copy from Lab to RBR-K (no access to modify RBR-K)

## Troubleshooting

### Problem: User can see all units
**Check:**
1. User is not admin (is_admin = False)
2. User has organizational_unit_id set
3. Clear browser cache and re-login

### Problem: Admin can't see any units
**Check:**
1. User has is_admin = True
2. Check database: `SELECT * FROM users WHERE username='admin'`

### Problem: Changes not visible
**Solution:**
1. Restart Flask application
2. Clear browser cache (Ctrl+Shift+Delete)
3. Try in incognito/private window

## Database Queries for Verification

```sql
-- Check user assignments
SELECT u.username, u.organizational_unit_id, l.name as org_unit_name
FROM users u
LEFT JOIN locations l ON u.organizational_unit_id = l.id;

-- Check all organizational units
SELECT id, name FROM locations ORDER BY name;

-- Count substances per unit
SELECT l.name, COUNT(s.id) as substance_count
FROM locations l
LEFT JOIN substances s ON l.id = s.location_id
GROUP BY l.name;
```

## Success Criteria

✓ Terminology changed from "Lokalizacja" to "Komórka organizacyjna"
✓ Admin can see and access all organizational units
✓ Regular users see only their assigned unit
✓ Access control prevents unauthorized access to other units
✓ Users can be assigned to units via admin interface
✓ Users without assignment cannot access any data

---
**Testing Date:** _______________
**Tester:** _______________
**Result:** PASS / FAIL
**Notes:**
