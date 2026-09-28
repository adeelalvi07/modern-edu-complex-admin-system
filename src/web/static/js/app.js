/**
 * Modern Educational Complex - School Management System
 * Production Client-Side Application Controller.
 */

// Application Global State
const State = {
  currentUser: null,
  classes: [],
  activeView: 'dashboard',
  attendanceRoster: [],
  marksRoster: [],
  selectedInvoice: null
};

// ==========================================================================
// UTILITY HELPERS
// ==========================================================================
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? '✔' : type === 'error' ? '✖' : 'ℹ';
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateX(40px)';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

function formatCurrency(amount) {
  return 'Rs. ' + Number(amount || 0).toLocaleString('en-PK', { minimumFractionDigits: 0, maximumFractionDigits: 0 });
}

function getTodayDate() {
  return new Date().toISOString().split('T')[0];
}

// ==========================================================================
// API REQUEST WRAPPER
// ==========================================================================
async function apiRequest(endpoint, options = {}) {
  const defaultHeaders = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  };

  const config = {
    ...options,
    headers: { ...defaultHeaders, ...options.headers }
  };

  if (options.body && typeof options.body === 'object') {
    config.body = JSON.stringify(options.body);
  }

  try {
    const res = await fetch(endpoint, config);
    if (res.status === 401) {
      // Session expired or unauthenticated
      if (State.currentUser) {
        showToast('Your session has expired. Please log in again.', 'error');
      }
      setAuthState(false);
      return null;
    }

    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.message || 'Server request failed');
    }
    return data;
  } catch (err) {
    showToast(err.message, 'error');
    throw err;
  }
}

// ==========================================================================
// AUTHENTICATION CONTROLLER
// ==========================================================================
function setAuthState(isAuthenticated, user = null, isDefaultPassword = false) {
  State.currentUser = user;
  State.isDefaultPassword = isDefaultPassword;
  const authWrapper = document.getElementById('auth-view');
  const appWrapper = document.getElementById('app-view');
  const warningBanner = document.getElementById('default-password-warning');

  if (isAuthenticated && user) {
    authWrapper.style.display = 'none';
    appWrapper.style.display = 'flex';

    document.getElementById('header-user-name').textContent = user.full_name || user.username;
    document.getElementById('header-user-role').textContent = user.role || 'Admin';
    document.getElementById('header-user-avatar').textContent = (user.full_name || user.username).charAt(0).toUpperCase();

    // Show or hide default password security warning
    if (warningBanner) {
      warningBanner.style.display = isDefaultPassword ? 'flex' : 'none';
    }

    // Initialize application data
    loadClasses();
    navigateTo('dashboard');
  } else {
    authWrapper.style.display = 'flex';
    appWrapper.style.display = 'none';
    if (warningBanner) warningBanner.style.display = 'none';
  }
}

async function checkAuthStatus() {
  try {
    const res = await fetch('/api/auth/me');
    if (res.ok) {
      const data = await res.json();
      setAuthState(true, data.user, data.is_default_password);
    } else {
      setAuthState(false);
    }
  } catch (e) {
    setAuthState(false);
  }
}

async function handleLogin(e) {
  e.preventDefault();
  const submitBtn = document.getElementById('login-submit-btn');
  const errorAlert = document.getElementById('login-error-alert');
  const username = document.getElementById('login-username').value.trim();
  const password = document.getElementById('login-password').value;
  const remember = document.getElementById('login-remember').checked;

  errorAlert.style.display = 'none';
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span>Verifying credentials...</span>';

  try {
    const res = await apiRequest('/api/auth/login', {
      method: 'POST',
      body: { username, password, remember }
    });

    if (res && res.success) {
      showToast(`Welcome back, ${res.user.full_name || res.user.username}!`, 'success');
      setAuthState(true, res.user, res.is_default_password);
    }
  } catch (err) {
    errorAlert.textContent = err.message || 'Login failed. Please check credentials.';
    errorAlert.style.display = 'flex';
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<span>Sign In to Admin Portal</span>';
  }
}

async function handleLogout() {
  if (!confirm('Are you sure you want to sign out?')) return;
  try {
    await apiRequest('/api/auth/logout', { method: 'POST' });
  } catch (e) {
    // Ignore error on logout
  }
  setAuthState(false);
  showToast('Signed out successfully.', 'info');
}

// ==========================================================================
// NAVIGATION & VIEW CONTROLLER
// ==========================================================================
function navigateTo(viewName) {
  State.activeView = viewName;

  // Update Nav items
  document.querySelectorAll('.nav-item').forEach(item => {
    item.classList.toggle('active', item.getAttribute('data-view') === viewName);
  });

  // Toggle Page Views
  document.querySelectorAll('.page-view').forEach(view => {
    view.classList.remove('active');
  });

  const targetView = document.getElementById(`view-${viewName}`);
  if (targetView) {
    targetView.classList.add('active');
  }

  // Close mobile sidebar if open
  document.querySelector('.app-sidebar').classList.remove('mobile-open');

  // Load specific view data
  switch (viewName) {
    case 'dashboard':
      loadDashboard();
      break;
    case 'students':
      loadStudents();
      break;
    case 'attendance':
      initAttendanceView();
      break;
    case 'fees':
      loadInvoices();
      break;
    case 'exams':
      initExamsView();
      break;
    case 'staff':
      loadStaff();
      break;
    case 'system':
      loadSystemView();
      break;
  }
}

// ==========================================================================
// CLASSES & SECTIONS CACHE
// ==========================================================================
async function loadClasses() {
  try {
    const res = await apiRequest('/api/students/classes/all');
    if (res && res.success) {
      State.classes = res.classes;
      populateClassDropdowns();
    }
  } catch (err) {
    console.error('Error loading classes:', err);
  }
}

function populateClassDropdowns() {
  const classDropdowns = document.querySelectorAll('.class-select-dropdown');
  classDropdowns.forEach(select => {
    const currentValue = select.value;
    select.innerHTML = '<option value="">All Classes</option>';
    State.classes.forEach(c => {
      const opt = document.createElement('option');
      opt.value = c.id;
      opt.textContent = c.name;
      select.appendChild(opt);
    });
    if (currentValue) select.value = currentValue;
  });
}

function onClassSelectionChange(classId, sectionSelectId) {
  const sectionSelect = document.getElementById(sectionSelectId);
  if (!sectionSelect) return;

  sectionSelect.innerHTML = '<option value="">All Sections</option>';
  const matched = State.classes.find(c => c.id == classId);
  if (matched && matched.sections) {
    matched.sections.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.id;
      opt.textContent = 'Section ' + s.name;
      sectionSelect.appendChild(opt);
    });
  }
}

// ==========================================================================
// 1. DASHBOARD MODULE
// ==========================================================================
async function loadDashboard() {
  try {
    const data = await apiRequest('/api/dashboard/stats');
    if (!data || !data.success) return;

    const kpis = data.kpis || {};
    const setElText = (id, text) => {
      const el = document.getElementById(id);
      if (el) el.textContent = text;
    };

    setElText('stat-total-students', kpis.total_students ?? 0);
    setElText('stat-total-staff', kpis.total_staff ?? 0);
    
    // Attendance KPI
    const att = kpis.attendance_today || {};
    setElText('stat-attendance-pct', `${att.percentage ?? 0}%`);
    setElText('stat-attendance-sub', 
      `${att.total_present ?? 0} Present / ${att.total_marked ?? 0} Marked (${att.classes_completed ?? 0}/${att.total_classes ?? 0} Classes)`);

    // Finance KPI
    const fin = kpis.finance_month || {};
    setElText('stat-month-collections', formatCurrency(fin.total_collected ?? 0));
    setElText('stat-month-pending', `${fin.collection_percentage ?? 0}% Collected (${formatCurrency(fin.total_invoiced ?? 0)} Invoiced)`);

    // Defaulters KPI
    const def = kpis.defaulters || {};
    setElText('stat-defaulters-count', def.count ?? 0);
    setElText('stat-defaulters-dues', `${formatCurrency(def.total_dues ?? 0)} Total Unpaid`);

    // Render Class Attendance Matrix
    renderDashboardClassAttendance(data.class_attendance_summary || []);

    // Load Recent Activity
    loadDashboardActivity();
  } catch (err) {
    console.error('Error loading dashboard stats:', err);
  }
}

function renderDashboardClassAttendance(summary) {
  const tbody = document.getElementById('dashboard-attendance-table-body');
  if (!tbody) return;

  if (!summary || summary.length === 0) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem;">No attendance data found.</td></tr>';
    return;
  }

  tbody.innerHTML = summary.map(row => {
    const badgeClass = row.status.includes('Completed') ? 'badge-success' : row.status.includes('Partial') ? 'badge-warning' : 'badge-danger';
    return `
      <tr>
        <td><strong>${row.display_class}</strong></td>
        <td>${row.total_enrolled}</td>
        <td>${row.marked_count}</td>
        <td><span class="badge badge-success">${row.present_count}</span></td>
        <td><span class="badge badge-danger">${row.absent_count}</span></td>
        <td><strong>${row.percentage}%</strong></td>
        <td><span class="badge ${badgeClass}">${row.status}</span></td>
      </tr>
    `;
  }).join('');
}

async function loadDashboardActivity() {
  try {
    const res = await apiRequest('/api/dashboard/recent-activity');
    if (!res || !res.success) return;

    const list = document.getElementById('dashboard-activity-list');
    if (!list) return;

    if (!res.logs || res.logs.length === 0) {
      list.innerHTML = '<p style="color:var(--text-muted); font-size:0.85rem;">No recent activities logged.</p>';
      return;
    }

    list.innerHTML = res.logs.slice(0, 8).map(log => `
      <div style="padding:0.75rem 0; border-bottom:1px solid var(--border-subtle); display:flex; justify-content:space-between; font-size:0.85rem;">
        <div>
          <strong style="color:var(--brand-primary);">${log.action}</strong>
          <span style="color:var(--text-secondary); margin-left:0.35rem;">${log.details || ''}</span>
        </div>
        <span style="color:var(--text-muted); font-size:0.75rem; white-space:nowrap;">${log.created_at || ''}</span>
      </div>
    `).join('');
  } catch (err) {
    console.error('Error loading activity:', err);
  }
}

// ==========================================================================
// 2. STUDENT MANAGEMENT MODULE
// ==========================================================================
async function loadStudents() {
  const search = document.getElementById('student-search-input').value.trim();
  const classId = document.getElementById('student-filter-class').value;
  const status = document.getElementById('student-filter-status').value;

  let url = `/api/students?status=${encodeURIComponent(status)}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (classId) url += `&class_id=${classId}`;

  const tbody = document.getElementById('students-table-body');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem;">Loading student records...</td></tr>';

  try {
    const res = await apiRequest(url);
    if (!res || !res.success) return;

    document.getElementById('students-count-badge').textContent = `${res.count} Students`;

    if (res.students.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem; color:var(--text-muted);">No students found matching filters.</td></tr>';
      return;
    }

    tbody.innerHTML = res.students.map(s => {
      const statusBadge = s.status === 'Active' ? 'badge-success' : s.status === 'Inactive' ? 'badge-warning' : 'badge-danger';
      const cleanName = `${s.first_name || ''} ${s.last_name || ''}`.replace(/'/g, "\\'");
      const admNo = (s.admission_number || '').replace(/'/g, "\\'");
      return `
        <tr>
          <td><strong style="font-family:var(--font-mono); color:var(--brand-gold);">${s.admission_number}</strong></td>
          <td>
            <div style="display:flex; align-items:center; gap:0.65rem;">
              <div class="avatar" style="width:28px; height:28px; font-size:0.75rem; background:var(--brand-gradient);">${(s.first_name || 'S').charAt(0)}</div>
              <strong>${s.first_name} ${s.last_name}</strong>
            </div>
          </td>
          <td>${s.class_name || '-'} (${s.section_name || '-'})</td>
          <td><strong>#${s.roll_number || '-'}</strong></td>
          <td>
            <div>${s.father_name || '-'}</div>
            <div style="font-size:0.78rem; color:var(--text-muted);">${s.father_phone || ''}</div>
          </td>
          <td><span class="badge ${statusBadge}">${s.status}</span></td>
          <td>
            <div class="action-btn-group">
              <button class="btn btn-sm btn-secondary" onclick="viewStudentDetails(${s.id})" title="View Profile">👁️ View</button>
              <button class="btn btn-sm btn-secondary" onclick="openEditStudentModal(${s.id})" title="Edit Details">✏️ Edit</button>
              <button class="btn btn-sm btn-outline-danger" onclick="openDeleteStudentModal(${s.id}, '${cleanName}', '${admNo}')" title="Delete Student">🗑️</button>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--danger); padding:2rem;">Failed to load students.</td></tr>';
  }
}

async function openRegisterStudentModal() {
  const modal = document.getElementById('modal-register-student');
  try {
    const res = await apiRequest('/api/students/next-admission-no');
    if (res && res.success) {
      document.getElementById('reg-adm-number').value = res.admission_number;
    }
  } catch (e) {}

  document.getElementById('reg-date').value = getTodayDate();
  populateClassDropdowns();
  modal.classList.add('open');
}

async function submitStudentRegistration(e) {
  e.preventDefault();
  const payload = {
    first_name: document.getElementById('reg-first-name').value.trim(),
    last_name: document.getElementById('reg-last-name').value.trim(),
    gender: document.getElementById('reg-gender').value,
    date_of_birth: document.getElementById('reg-dob').value,
    blood_group: document.getElementById('reg-blood-group').value,
    religion: document.getElementById('reg-religion').value,
    admission_number: document.getElementById('reg-adm-number').value.trim(),
    registration_date: document.getElementById('reg-date').value,
    father_name: document.getElementById('reg-father-name').value.trim(),
    father_phone: document.getElementById('reg-father-phone').value.trim(),
    father_cnic_nid: document.getElementById('reg-father-cnic').value.trim(),
    father_occupation: document.getElementById('reg-father-occupation').value.trim(),
    emergency_contact: document.getElementById('reg-emergency-phone').value.trim(),
    residential_address: document.getElementById('reg-address').value.trim(),
    class_id: parseInt(document.getElementById('reg-class-id').value),
    section_id: parseInt(document.getElementById('reg-section-id').value),
    roll_number: parseInt(document.getElementById('reg-roll-number').value)
  };

  try {
    const res = await apiRequest('/api/students/register', {
      method: 'POST',
      body: payload
    });
    if (res && res.success) {
      showToast(res.message, 'success');
      closeModal('modal-register-student');
      document.getElementById('form-register-student').reset();
      loadStudents();
      loadDashboard();
    }
  } catch (err) {}
}

async function viewStudentDetails(studentId) {
  try {
    const res = await apiRequest(`/api/students/${studentId}`);
    if (!res || !res.success) return;

    const s = res.student;
    const att = res.attendance || {};
    State.currentStudent = s;

    const modal = document.getElementById('modal-student-profile');

    document.getElementById('prof-name').textContent = `${s.first_name} ${s.last_name}`;
    document.getElementById('prof-adm').textContent = s.admission_number;
    document.getElementById('prof-class').textContent = `${s.class_name} - ${s.section_name} (Roll #${s.roll_number})`;
    document.getElementById('prof-father').textContent = s.father_name || '--';
    document.getElementById('prof-contact').textContent = `${s.father_phone || ''} ${s.emergency_contact ? '• Em: ' + s.emergency_contact : ''}`;
    document.getElementById('prof-address').textContent = s.residential_address || 'Not specified';
    document.getElementById('prof-att-pct').textContent = `${att.percentage || 0}%`;
    document.getElementById('prof-att-stats').textContent = `${att.present_days || 0} Present / ${att.total_days || 0} Days`;

    const statusBadge = document.getElementById('prof-status-badge');
    if (statusBadge) {
      statusBadge.textContent = s.status || 'Active';
      statusBadge.className = `badge ${s.status === 'Active' ? 'badge-success' : s.status === 'Inactive' ? 'badge-warning' : 'badge-danger'}`;
    }

    // Render Recent Invoices
    const invBody = document.getElementById('prof-invoices-body');
    if (!res.invoices || res.invoices.length === 0) {
      invBody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:1.5rem; color:var(--text-muted);">No fee records found.</td></tr>';
    } else {
      invBody.innerHTML = res.invoices.map(inv => `
        <tr>
          <td><strong style="color:var(--brand-gold);">${inv.invoice_number}</strong></td>
          <td>${inv.billing_month}/${inv.billing_year}</td>
          <td>${formatCurrency(inv.net_payable)}</td>
          <td>${formatCurrency(inv.balance_amount)}</td>
          <td><span class="badge ${inv.status === 'Paid' ? 'badge-success' : 'badge-danger'}">${inv.status}</span></td>
        </tr>
      `).join('');
    }

    modal.classList.add('open');
  } catch (err) {
    console.error(err);
  }
}

function editStudentFromProfile() {
  if (State.currentStudent) {
    closeModal('modal-student-profile');
    openEditStudentModal(State.currentStudent.id);
  }
}

function deleteStudentFromProfile() {
  if (State.currentStudent) {
    const s = State.currentStudent;
    closeModal('modal-student-profile');
    openDeleteStudentModal(s.id, `${s.first_name} ${s.last_name}`, s.admission_number);
  }
}

async function openEditStudentModal(studentId) {
  try {
    const res = await apiRequest(`/api/students/${studentId}`);
    if (!res || !res.success) return;

    const s = res.student;
    State.currentEditStudentId = studentId;

    document.getElementById('edit-student-id').value = s.id;
    document.getElementById('edit-adm-display').textContent = s.admission_number;
    document.getElementById('edit-status').value = s.status || 'Active';

    // Demographics
    document.getElementById('edit-first-name').value = s.first_name || '';
    document.getElementById('edit-last-name').value = s.last_name || '';
    document.getElementById('edit-gender').value = s.gender || 'Male';
    document.getElementById('edit-dob').value = s.date_of_birth ? s.date_of_birth.substring(0, 10) : '';
    document.getElementById('edit-blood-group').value = s.blood_group || 'O+';
    document.getElementById('edit-religion').value = s.religion || 'Islam';

    // Parent
    document.getElementById('edit-father-name').value = s.father_name || '';
    document.getElementById('edit-father-phone').value = s.father_phone || '';
    document.getElementById('edit-father-cnic').value = s.father_cnic_nid || '';
    document.getElementById('edit-father-occupation').value = s.father_occupation || '';
    document.getElementById('edit-emergency-contact').value = s.emergency_contact || '';
    document.getElementById('edit-mother-name').value = s.mother_name || '';
    document.getElementById('edit-father-email').value = s.father_email || '';
    document.getElementById('edit-address').value = s.residential_address || '';

    // Classes & Sections
    populateClassDropdowns();
    const classSelect = document.getElementById('edit-class-id');
    classSelect.value = s.class_id || '';
    if (s.class_id) {
      onClassSelectionChange(s.class_id, 'edit-section-id');
      document.getElementById('edit-section-id').value = s.section_id || '';
    }
    document.getElementById('edit-roll-number').value = s.roll_number || 1;

    document.getElementById('modal-edit-student').classList.add('open');
  } catch (err) {
    showToast('Failed to load student details for editing', 'danger');
  }
}

async function submitEditStudent(e) {
  e.preventDefault();
  const studentId = document.getElementById('edit-student-id').value;
  const payload = {
    first_name: document.getElementById('edit-first-name').value.trim(),
    last_name: document.getElementById('edit-last-name').value.trim(),
    gender: document.getElementById('edit-gender').value,
    date_of_birth: document.getElementById('edit-dob').value,
    blood_group: document.getElementById('edit-blood-group').value,
    religion: document.getElementById('edit-religion').value.trim(),
    status: document.getElementById('edit-status').value,
    father_name: document.getElementById('edit-father-name').value.trim(),
    father_phone: document.getElementById('edit-father-phone').value.trim(),
    father_cnic_nid: document.getElementById('edit-father-cnic').value.trim() || null,
    father_occupation: document.getElementById('edit-father-occupation').value.trim() || null,
    emergency_contact: document.getElementById('edit-emergency-contact').value.trim(),
    mother_name: document.getElementById('edit-mother-name').value.trim() || null,
    father_email: document.getElementById('edit-father-email').value.trim() || null,
    residential_address: document.getElementById('edit-address').value.trim(),
    class_id: parseInt(document.getElementById('edit-class-id').value) || null,
    section_id: parseInt(document.getElementById('edit-section-id').value) || null,
    roll_number: parseInt(document.getElementById('edit-roll-number').value) || null
  };

  try {
    const res = await apiRequest(`/api/students/${studentId}`, {
      method: 'PUT',
      body: payload
    });
    if (res && res.success) {
      showToast('Student information updated successfully!', 'success');
      closeModal('modal-edit-student');
      loadStudents();
      loadDashboard();
    }
  } catch (err) {}
}

function openDeleteStudentModal(studentId, name, adm) {
  document.getElementById('del-student-id').value = studentId;
  document.getElementById('del-student-name').textContent = name;
  document.getElementById('del-student-adm').textContent = adm;
  document.getElementById('modal-delete-student').classList.add('open');
}

async function confirmPermanentDeleteStudent() {
  const studentId = document.getElementById('del-student-id').value;
  if (!studentId) return;

  try {
    const res = await apiRequest(`/api/students/${studentId}`, {
      method: 'DELETE'
    });
    if (res && res.success) {
      showToast(res.message || 'Student permanently deleted.', 'success');
      closeModal('modal-delete-student');
      closeModal('modal-student-profile');
      loadStudents();
      loadDashboard();
    }
  } catch (err) {}
}

async function confirmDeactivateStudent() {
  const studentId = document.getElementById('del-student-id').value;
  if (!studentId) return;

  try {
    const res = await apiRequest(`/api/students/${studentId}/status`, {
      method: 'PATCH',
      body: { status: 'Inactive', remarks: 'Deactivated by administrator from web portal' }
    });
    if (res && res.success) {
      showToast('Student status marked as Inactive.', 'info');
      closeModal('modal-delete-student');
      loadStudents();
      loadDashboard();
    }
  } catch (err) {}
}

// ==========================================================================
// 3. ATTENDANCE MODULE
// ==========================================================================
function initAttendanceView() {
  document.getElementById('att-target-date').value = getTodayDate();
  populateClassDropdowns();
  // Auto-select first class if available
  const classSelect = document.getElementById('att-select-class');
  if (State.classes.length > 0 && !classSelect.value) {
    classSelect.value = State.classes[0].id;
    onClassSelectionChange(State.classes[0].id, 'att-select-section');
    const secSelect = document.getElementById('att-select-section');
    if (secSelect.options.length > 1) secSelect.selectedIndex = 1;
    loadAttendanceRoster();
  }
}

async function loadAttendanceRoster() {
  const classId = document.getElementById('att-select-class').value;
  const sectionId = document.getElementById('att-select-section').value;
  const targetDate = document.getElementById('att-target-date').value;

  if (!classId || !sectionId) {
    showToast('Please select both Class and Section.', 'info');
    return;
  }

  const tbody = document.getElementById('attendance-roster-body');
  tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem;">Loading roster...</td></tr>';

  try {
    const res = await apiRequest(`/api/attendance/roster?class_id=${classId}&section_id=${sectionId}&attendance_date=${targetDate}`);
    if (!res || !res.success) return;

    State.attendanceRoster = res.students;
    renderAttendanceRoster();
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; color:var(--danger); padding:2rem;">Failed to load roster.</td></tr>';
  }
}

function renderAttendanceRoster() {
  const tbody = document.getElementById('attendance-roster-body');
  if (State.attendanceRoster.length === 0) {
    tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:2rem;">No students found in this class section.</td></tr>';
    updateAttendanceCounters();
    return;
  }

  tbody.innerHTML = State.attendanceRoster.map((st, idx) => `
    <tr>
      <td><strong>${st.roll_number}</strong></td>
      <td><span style="font-family:var(--font-mono);">${st.admission_number}</span></td>
      <td><strong>${st.first_name} ${st.last_name}</strong></td>
      <td>
        <div class="attendance-pills">
          <button type="button" class="att-pill ${st.status === 'Present' ? 'active-P' : ''}" onclick="setStudentStatus(${idx}, 'Present')">P</button>
          <button type="button" class="att-pill ${st.status === 'Absent' ? 'active-A' : ''}" onclick="setStudentStatus(${idx}, 'Absent')">A</button>
          <button type="button" class="att-pill ${st.status === 'Late' ? 'active-L' : ''}" onclick="setStudentStatus(${idx}, 'Late')">L</button>
          <button type="button" class="att-pill ${st.status === 'Half Day' ? 'active-HD' : ''}" onclick="setStudentStatus(${idx}, 'Half Day')">HD</button>
          <button type="button" class="att-pill ${st.status === 'Excused' ? 'active-E' : ''}" onclick="setStudentStatus(${idx}, 'Excused')">E</button>
        </div>
      </td>
      <td>
        <input type="text" class="form-input" style="padding:0.35rem 0.65rem; font-size:0.8rem;" 
               placeholder="Remarks..." value="${st.remarks || ''}" 
               onchange="setStudentRemarks(${idx}, this.value)">
      </td>
    </tr>
  `).join('');

  updateAttendanceCounters();
}

function setStudentStatus(index, newStatus) {
  if (State.attendanceRoster[index]) {
    State.attendanceRoster[index].status = newStatus;
    renderAttendanceRoster();
  }
}

function setStudentRemarks(index, remarks) {
  if (State.attendanceRoster[index]) {
    State.attendanceRoster[index].remarks = remarks;
  }
}

function markAllPresent() {
  State.attendanceRoster.forEach(st => st.status = 'Present');
  renderAttendanceRoster();
  showToast('Marked all students as Present!', 'success');
}

function updateAttendanceCounters() {
  const total = State.attendanceRoster.length;
  const present = State.attendanceRoster.filter(s => s.status === 'Present').length;
  const absent = State.attendanceRoster.filter(s => s.status === 'Absent').length;
  const late = State.attendanceRoster.filter(s => s.status === 'Late').length;

  document.getElementById('att-count-total').textContent = total;
  document.getElementById('att-count-present').textContent = present;
  document.getElementById('att-count-absent').textContent = absent;
  document.getElementById('att-count-late').textContent = late;
}

async function saveBatchAttendance() {
  const classId = parseInt(document.getElementById('att-select-class').value);
  const sectionId = parseInt(document.getElementById('att-select-section').value);
  const targetDate = document.getElementById('att-target-date').value;

  if (State.attendanceRoster.length === 0) {
    showToast('No students to save.', 'info');
    return;
  }

  const payload = {
    class_id: classId,
    section_id: sectionId,
    attendance_date: targetDate,
    records: State.attendanceRoster.map(s => ({
      student_id: s.student_id,
      status: s.status,
      remarks: s.remarks
    }))
  };

  try {
    const res = await apiRequest('/api/attendance/save-batch', {
      method: 'POST',
      body: payload
    });
    if (res && res.success) {
      showToast(res.message, 'success');
    }
  } catch (err) {}
}

async function loadChronicAbsentees() {
  try {
    const res = await apiRequest('/api/attendance/chronic-absentees?threshold=75');
    if (!res || !res.success) return;

    const tbody = document.getElementById('chronic-table-body');
    if (res.absentees.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem; color:var(--success);">✔ No chronic absentees detected!</td></tr>';
      return;
    }

    tbody.innerHTML = res.absentees.map(a => `
      <tr>
        <td><strong>${a.admission_number}</strong></td>
        <td><strong>${a.first_name} ${a.last_name}</strong></td>
        <td>${a.class_name} - ${a.section_name}</td>
        <td>${a.father_name} (${a.father_phone})</td>
        <td>${a.present_days} / ${a.total_days}</td>
        <td><strong style="color:var(--danger);">${a.percentage}%</strong></td>
        <td><span class="badge badge-danger">Below 75%</span></td>
      </tr>
    `).join('');
  } catch (err) {}
}

// ==========================================================================
// 4. FEES & BILLING MODULE
// ==========================================================================
async function loadInvoices() {
  const search = document.getElementById('fee-search-input').value.trim();
  const classId = document.getElementById('fee-filter-class').value;
  const status = document.getElementById('fee-filter-status').value;

  let url = `/api/fees/invoices?status=${encodeURIComponent(status)}`;
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (classId) url += `&class_id=${classId}`;

  const tbody = document.getElementById('fees-invoices-body');
  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2rem;">Loading invoice records...</td></tr>';

  try {
    const res = await apiRequest(url);
    if (!res || !res.success) return;

    if (res.invoices.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2rem;">No invoices found.</td></tr>';
      return;
    }

    tbody.innerHTML = res.invoices.map(inv => {
      const isPaid = inv.status === 'Paid';
      const statusBadge = isPaid ? 'badge-success' : inv.status === 'Partially Paid' ? 'badge-warning' : 'badge-danger';
      return `
        <tr>
          <td><strong style="font-family:var(--font-mono); color:var(--brand-primary);">${inv.invoice_number}</strong></td>
          <td>
            <strong>${inv.first_name} ${inv.last_name}</strong>
            <div style="font-size:0.75rem; color:var(--text-muted);">${inv.admission_number}</div>
          </td>
          <td>${inv.class_name} (${inv.section_name})</td>
          <td>${inv.billing_month}/${inv.billing_year}</td>
          <td>${formatCurrency(inv.net_payable)}</td>
          <td><strong style="color:${isPaid ? 'var(--text-muted)' : 'var(--danger)'};">${formatCurrency(inv.balance_amount)}</strong></td>
          <td><span class="badge ${statusBadge}">${inv.status}</span></td>
          <td>
            <div style="display:flex; gap:0.4rem;">
              ${!isPaid ? `<button class="btn btn-sm btn-success" onclick="openPaymentModal(${inv.id}, '${inv.invoice_number}', '${inv.first_name} ${inv.last_name}', ${inv.balance_amount})">Pay</button>` : ''}
              <a href="/api/fees/invoice/${inv.id}/pdf" target="_blank" class="btn btn-sm btn-secondary">Challan PDF</a>
            </div>
          </td>
        </tr>
      `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--danger); padding:2rem;">Failed to load invoices.</td></tr>';
  }
}

function openPaymentModal(invoiceId, invoiceNumber, studentName, balance) {
  document.getElementById('pay-invoice-id').value = invoiceId;
  document.getElementById('pay-invoice-label').textContent = `${invoiceNumber} (${studentName})`;
  document.getElementById('pay-balance-label').textContent = formatCurrency(balance);
  document.getElementById('pay-amount').value = balance;
  document.getElementById('pay-date').value = getTodayDate();
  document.getElementById('modal-fee-payment').classList.add('open');
}

async function submitFeePayment(e) {
  e.preventDefault();
  const invoiceId = parseInt(document.getElementById('pay-invoice-id').value);
  const amountPaid = parseFloat(document.getElementById('pay-amount').value);
  const paymentMode = document.getElementById('pay-mode').value;
  const ref = document.getElementById('pay-ref').value.trim();
  const remarks = document.getElementById('pay-remarks').value.trim();
  const paymentDate = document.getElementById('pay-date').value;

  try {
    const res = await apiRequest('/api/fees/pay', {
      method: 'POST',
      body: {
        invoice_id: invoiceId,
        amount_paid: amountPaid,
        payment_mode: paymentMode,
        reference_number: ref,
        remarks: remarks,
        payment_date: paymentDate
      }
    });

    if (res && res.success) {
      showToast(res.message, 'success');
      closeModal('modal-fee-payment');
      loadInvoices();
    }
  } catch (err) {}
}

async function openGenerateVouchersModal() {
  populateClassDropdowns();
  const now = new Date();
  document.getElementById('gen-month').value = now.getMonth() + 1;
  document.getElementById('gen-year').value = now.getFullYear();
  
  // Default due date: 10th of next month
  const dueDate = new Date(now.getFullYear(), now.getMonth(), 10);
  document.getElementById('gen-due-date').value = dueDate.toISOString().split('T')[0];

  document.getElementById('modal-generate-vouchers').classList.add('open');
}

async function submitGenerateVouchers(e) {
  e.preventDefault();
  const classId = parseInt(document.getElementById('gen-class-id').value);
  const month = parseInt(document.getElementById('gen-month').value);
  const year = parseInt(document.getElementById('gen-year').value);
  const dueDate = document.getElementById('gen-due-date').value;

  try {
    const res = await apiRequest('/api/fees/vouchers/generate', {
      method: 'POST',
      body: {
        class_id: classId,
        billing_month: month,
        billing_year: year,
        due_date: dueDate
      }
    });
    if (res && res.success) {
      showToast(res.message, 'success');
      closeModal('modal-generate-vouchers');
      loadInvoices();
    }
  } catch (err) {}
}

async function loadDefaulters() {
  const tbody = document.getElementById('defaulters-table-body');
  tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; padding:2rem;">Loading defaulters register...</td></tr>';

  try {
    const res = await apiRequest('/api/fees/defaulters');
    if (!res || !res.success) return;

    document.getElementById('defaulters-total-banner').textContent = 
      `Total Defaulters: ${res.count} Students | Total Outstanding: ${formatCurrency(res.total_dues)}`;

    if (res.defaulters.length === 0) {
      tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--success); padding:2rem;">✔ All accounts settled! No outstanding defaulters.</td></tr>';
      return;
    }

    tbody.innerHTML = res.defaulters.map(d => `
      <tr>
        <td><strong>${d.invoice_number}</strong></td>
        <td><strong>${d.first_name} ${d.last_name}</strong> (${d.admission_number})</td>
        <td>${d.class_name} - ${d.section_name}</td>
        <td>${d.father_name} (${d.father_phone})</td>
        <td>${d.billing_month}/${d.billing_year}</td>
        <td><strong style="color:var(--danger);">${formatCurrency(d.balance_amount)}</strong></td>
        <td>
          <button class="btn btn-sm btn-success" onclick="openPaymentModal(${d.id}, '${d.invoice_number}', '${d.first_name} ${d.last_name}', ${d.balance_amount})">Collect</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="7" style="text-align:center; color:var(--danger);">Failed to load defaulters.</td></tr>';
  }
}

// ==========================================================================
// 5. EXAMS & ACADEMIC RESULTS MODULE
// ==========================================================================
async function initExamsView() {
  populateClassDropdowns();
  try {
    const res = await apiRequest('/api/exams');
    if (res && res.success) {
      const examSelect = document.getElementById('exam-select-term');
      examSelect.innerHTML = '<option value="">Select Exam Term</option>';
      res.exams.forEach(e => {
        const opt = document.createElement('option');
        opt.value = e.id;
        opt.textContent = `${e.name} (${e.status})`;
        examSelect.appendChild(opt);
      });
      if (res.exams.length > 0) {
        examSelect.selectedIndex = 1;
        onExamClassChange();
      }
    }
  } catch (err) {}
}

async function onExamClassChange() {
  const examId = document.getElementById('exam-select-term').value;
  const classId = document.getElementById('exam-select-class').value;
  const subjectSelect = document.getElementById('exam-select-subject');

  if (!examId || !classId) return;

  try {
    const res = await apiRequest(`/api/exams/${examId}/subjects?class_id=${classId}`);
    if (res && res.success) {
      subjectSelect.innerHTML = '<option value="">Select Subject</option>';
      res.scheduled_subjects.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s.id; // exam_subject_id
        opt.textContent = `${s.subject_name} (Max: ${s.max_marks})`;
        subjectSelect.appendChild(opt);
      });
      if (res.scheduled_subjects.length > 0) {
        subjectSelect.selectedIndex = 1;
      }
    }
  } catch (err) {}
}

async function loadMarksRoster() {
  const examSubjectId = document.getElementById('exam-select-subject').value;
  const classId = document.getElementById('exam-select-class').value;
  const sectionId = document.getElementById('exam-select-section').value;

  if (!examSubjectId || !classId || !sectionId) {
    showToast('Please select Exam Term, Class, Section, and Subject.', 'info');
    return;
  }

  const tbody = document.getElementById('exam-marks-roster-body');
  tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem;">Loading students for marking...</td></tr>';

  try {
    const res = await apiRequest(`/api/exams/marks/roster?exam_subject_id=${examSubjectId}&class_id=${classId}&section_id=${sectionId}`);
    if (!res || !res.success) return;

    State.marksRoster = res.students;
    renderMarksRoster();
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:var(--danger); padding:2rem;">Failed to load marks roster.</td></tr>';
  }
}

function calculateGrade(marks, max = 100) {
  const pct = (marks / max) * 100;
  if (pct >= 85) return 'A+';
  if (pct >= 75) return 'A';
  if (pct >= 65) return 'B';
  if (pct >= 50) return 'C';
  if (pct >= 40) return 'D';
  return 'F';
}

function renderMarksRoster() {
  const tbody = document.getElementById('exam-marks-roster-body');
  if (State.marksRoster.length === 0) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:2rem;">No students found for marking.</td></tr>';
    return;
  }

  tbody.innerHTML = State.marksRoster.map((st, idx) => {
    const grade = st.is_absent ? 'ABS' : (st.grade || calculateGrade(st.marks_obtained || 0));
    const gradeColor = grade === 'A+' || grade === 'A' ? 'var(--success)' : grade === 'F' || grade === 'ABS' ? 'var(--danger)' : 'var(--brand-primary)';

    return `
      <tr>
        <td><strong>${st.roll_number}</strong></td>
        <td>${st.admission_number}</td>
        <td><strong>${st.first_name} ${st.last_name}</strong></td>
        <td>
          <input type="number" step="0.5" min="0" max="100" class="form-input" 
                 style="width:90px; padding:0.35rem 0.5rem;" 
                 value="${st.marks_obtained || 0}" 
                 ${st.is_absent ? 'disabled' : ''}
                 onchange="updateStudentMark(${idx}, this.value)">
        </td>
        <td>
          <label style="display:flex; align-items:center; gap:0.4rem; cursor:pointer;">
            <input type="checkbox" ${st.is_absent ? 'checked' : ''} 
                   onchange="toggleStudentAbsent(${idx}, this.checked)">
            <span style="font-size:0.8rem;">Absent</span>
          </label>
        </td>
        <td><strong style="color:${gradeColor}; font-size:1.05rem;">${grade}</strong></td>
      </tr>
    `;
  }).join('');
}

function updateStudentMark(index, val) {
  if (State.marksRoster[index]) {
    State.marksRoster[index].marks_obtained = parseFloat(val) || 0;
    State.marksRoster[index].grade = calculateGrade(State.marksRoster[index].marks_obtained);
    renderMarksRoster();
  }
}

function toggleStudentAbsent(index, isAbsent) {
  if (State.marksRoster[index]) {
    State.marksRoster[index].is_absent = isAbsent;
    if (isAbsent) State.marksRoster[index].grade = 'ABS';
    renderMarksRoster();
  }
}

async function saveBatchMarks() {
  const examSubjectId = parseInt(document.getElementById('exam-select-subject').value);
  if (!examSubjectId || State.marksRoster.length === 0) return;

  const payload = {
    exam_subject_id: examSubjectId,
    records: State.marksRoster.map(s => ({
      student_id: s.student_id,
      marks_obtained: s.marks_obtained,
      is_absent: Boolean(s.is_absent),
      teacher_remarks: s.teacher_remarks
    }))
  };

  try {
    const res = await apiRequest('/api/exams/marks/save-batch', {
      method: 'POST',
      body: payload
    });
    if (res && res.success) {
      showToast(res.message, 'success');
    }
  } catch (err) {}
}

// ==========================================================================
// 6. STAFF & FACULTY MODULE
// ==========================================================================
async function loadStaff() {
  const search = document.getElementById('staff-search-input').value.trim();
  const deptId = document.getElementById('staff-filter-dept').value;

  let url = '/api/staff?status=Active';
  if (search) url += `&search=${encodeURIComponent(search)}`;
  if (deptId) url += `&department_id=${deptId}`;

  const tbody = document.getElementById('staff-table-body');
  tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2rem;">Loading faculty records...</td></tr>';

  try {
    const res = await apiRequest(url);
    if (!res || !res.success) return;

    if (res.staff.length === 0) {
      tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; padding:2rem;">No staff members found.</td></tr>';
      return;
    }

    tbody.innerHTML = res.staff.map(st => {
      const cleanName = `${st.first_name || ''} ${st.last_name || ''}`.replace(/'/g, "\\'");
      return `
      <tr>
        <td><strong style="font-family:var(--font-mono); color:var(--brand-gold);">${st.employee_code}</strong></td>
        <td>
          <div style="display:flex; align-items:center; gap:0.65rem;">
            <div class="avatar" style="width:28px; height:28px; font-size:0.75rem; background:var(--brand-gradient);">${st.first_name.charAt(0)}</div>
            <strong>${st.first_name} ${st.last_name}</strong>
          </div>
        </td>
        <td>${st.designation}</td>
        <td><span class="badge badge-info">${st.department_name}</span></td>
        <td>${st.contact_phone}</td>
        <td>${formatCurrency(st.basic_salary)}</td>
        <td><span class="badge badge-success">Active</span></td>
        <td>
          <div class="action-btn-group">
            <button class="btn btn-sm btn-outline-danger" onclick="openDeleteStaffModal(${st.id}, '${cleanName}')" title="Delete Staff Member">🗑️ Delete</button>
          </div>
        </td>
      </tr>
    `;
    }).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center; color:var(--danger);">Failed to load staff.</td></tr>';
  }
}

function openDeleteStaffModal(staffId, staffName) {
  document.getElementById('del-staff-id').value = staffId;
  document.getElementById('del-staff-name').textContent = staffName;
  document.getElementById('modal-delete-staff').classList.add('open');
}

async function confirmDeleteStaff() {
  const staffId = document.getElementById('del-staff-id').value;
  if (!staffId) return;

  try {
    const res = await apiRequest(`/api/staff/${staffId}`, {
      method: 'DELETE'
    });
    if (res && res.success) {
      showToast(res.message || 'Staff member permanently deleted.', 'success');
      closeModal('modal-delete-staff');
      loadStaff();
      loadDashboard();
    }
  } catch (err) {}
}

function openAddStaffModal() {
  document.getElementById('modal-add-staff').classList.add('open');
}

async function submitAddStaff(e) {
  e.preventDefault();
  const payload = {
    first_name: document.getElementById('staff-first-name').value.trim(),
    last_name: document.getElementById('staff-last-name').value.trim(),
    gender: document.getElementById('staff-gender').value,
    date_of_birth: document.getElementById('staff-dob').value,
    department_id: parseInt(document.getElementById('staff-dept-id').value),
    designation: document.getElementById('staff-designation').value.trim(),
    contact_phone: document.getElementById('staff-phone').value.trim(),
    email: document.getElementById('staff-email').value.trim() || null,
    qualification: document.getElementById('staff-qualification').value.trim() || null,
    basic_salary: parseFloat(document.getElementById('staff-salary').value) || 0
  };

  try {
    const res = await apiRequest('/api/staff', {
      method: 'POST',
      body: payload
    });
    if (res && res.success) {
      showToast(res.message, 'success');
      closeModal('modal-add-staff');
      document.getElementById('form-add-staff').reset();
      loadStaff();
    }
  } catch (err) {}
}

// ==========================================================================
// 7. SYSTEM, BACKUPS & AUDIT LOGS MODULE
// ==========================================================================
async function loadSystemView() {
  loadBackups();
  loadAuditLogs();
}

async function loadBackups() {
  const tbody = document.getElementById('backups-table-body');
  try {
    const res = await apiRequest('/api/system/backups');
    if (!res || !res.success) return;

    if (res.backups.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:1.5rem;">No backup archives generated yet.</td></tr>';
      return;
    }

    tbody.innerHTML = res.backups.map(b => `
      <tr>
        <td><strong>${b.filename}</strong></td>
        <td>${b.size_mb} MB</td>
        <td>${b.created_at}</td>
        <td>
          <a href="/api/system/backups/${encodeURIComponent(b.filename)}/download" class="btn btn-sm btn-primary">Download Archive</a>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:var(--danger);">Failed to load backups.</td></tr>';
  }
}

async function createInstantBackup() {
  const btn = document.getElementById('btn-instant-backup');
  btn.disabled = true;
  btn.innerHTML = '<span>Creating backup archive...</span>';

  try {
    const res = await apiRequest('/api/system/backup/create', { method: 'POST' });
    if (res && res.success) {
      showToast(res.message, 'success');
      loadBackups();
    }
  } catch (err) {
  } finally {
    btn.disabled = false;
    btn.innerHTML = '<span>Create Instant Backup Now</span>';
  }
}

async function loadAuditLogs() {
  const tbody = document.getElementById('audit-logs-table-body');
  try {
    const res = await apiRequest('/api/system/audit-logs?limit=40');
    if (!res || !res.success) return;

    if (res.logs.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" style="text-align:center; padding:1.5rem;">No audit records found.</td></tr>';
      return;
    }

    tbody.innerHTML = res.logs.map(log => `
      <tr>
        <td style="font-size:0.75rem; color:var(--text-muted);">${log.created_at}</td>
        <td><strong style="color:var(--brand-primary);">${log.action}</strong></td>
        <td><span class="badge badge-info">${log.module}</span></td>
        <td>${log.details || '-'}</td>
        <td style="font-size:0.78rem;">${log.username || 'System'}</td>
      </tr>
    `).join('');
  } catch (err) {}
}

// ==========================================================================
// MODAL CONTROLLER
// ==========================================================================
function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) modal.classList.remove('open');
}

// Close modal on escape key or backdrop click
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    document.querySelectorAll('.modal-overlay.open').forEach(m => m.classList.remove('open'));
  }
});

document.addEventListener('click', e => {
  if (e.target.classList.contains('modal-overlay')) {
    e.target.classList.remove('open');
  }
});

// ==========================================================================
// THEME CONTROLLER
// ==========================================================================
function toggleTheme() {
  const currentTheme = document.documentElement.getAttribute('data-theme') || 'dark';
  const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', newTheme);
  localStorage.setItem('sms_theme', newTheme);
}

function initTheme() {
  const saved = localStorage.getItem('sms_theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
}

// ==========================================================================
// CLOCK CONTROLLER
// ==========================================================================
function updateClock() {
  const clockEl = document.getElementById('header-live-clock');
  if (!clockEl) return;
  const now = new Date();
  const timeStr = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const dateStr = now.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
  clockEl.innerHTML = `<span class="clock-time">${timeStr}</span><span>${dateStr}</span>`;
}

// ==========================================================================
// INITIALIZATION ON DOM READY
// ==========================================================================
document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  setInterval(updateClock, 1000);
  updateClock();

  // Check current session
  checkAuthStatus();

  // Login form listener
  const loginForm = document.getElementById('login-form');
  if (loginForm) loginForm.addEventListener('submit', handleLogin);

  // Password toggle
  const pwdToggle = document.getElementById('password-toggle-btn');
  if (pwdToggle) {
    pwdToggle.addEventListener('click', () => {
      const pwdInput = document.getElementById('login-password');
      pwdInput.type = pwdInput.type === 'password' ? 'text' : 'password';
    });
  }

  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebar-toggle-btn');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => {
      document.querySelector('.app-sidebar').classList.toggle('mobile-open');
    });
  }
});

// ==========================================================================
// SECURITY & ACCOUNT SETTINGS CONTROLLER
// ==========================================================================
function openSecuritySettingsModal() {
  const user = State.currentUser;
  if (!user) return;

  // Pre-fill profile fields
  document.getElementById('sec-username').value = user.username || '';
  document.getElementById('sec-fullname').value = user.full_name || '';
  document.getElementById('sec-email').value = user.email || '';

  // Clear password inputs and alerts
  document.getElementById('sec-old-password').value = '';
  document.getElementById('sec-new-password').value = '';
  document.getElementById('sec-confirm-password').value = '';
  document.getElementById('pwd-change-alert').style.display = 'none';
  document.getElementById('profile-update-alert').style.display = 'none';

  switchSecurityTab('pwd');
  openModal('modal-security-settings');
}

function switchSecurityTab(tab) {
  const pwdForm = document.getElementById('form-change-password');
  const profileForm = document.getElementById('form-update-profile');
  const btnPwd = document.getElementById('sec-tab-btn-pwd');
  const btnProfile = document.getElementById('sec-tab-btn-profile');

  if (tab === 'pwd') {
    pwdForm.style.display = 'block';
    profileForm.style.display = 'none';
    btnPwd.className = 'btn btn-primary btn-sm';
    btnProfile.className = 'btn btn-secondary btn-sm';
  } else {
    pwdForm.style.display = 'none';
    profileForm.style.display = 'block';
    btnPwd.className = 'btn btn-secondary btn-sm';
    btnProfile.className = 'btn btn-primary btn-sm';
  }
}

async function submitChangePassword(e) {
  e.preventDefault();
  const alertBox = document.getElementById('pwd-change-alert');
  const submitBtn = document.getElementById('btn-submit-pwd');
  const old_password = document.getElementById('sec-old-password').value;
  const new_password = document.getElementById('sec-new-password').value;
  const confirm_password = document.getElementById('sec-confirm-password').value;

  alertBox.style.display = 'none';

  if (new_password !== confirm_password) {
    alertBox.textContent = 'New password and confirmation password do not match.';
    alertBox.style.display = 'block';
    return;
  }

  submitBtn.disabled = true;
  submitBtn.textContent = 'Updating...';

  try {
    const res = await apiRequest('/api/auth/change-password', {
      method: 'POST',
      body: { old_password, new_password, confirm_password }
    });

    if (res && res.success) {
      showToast('Password changed successfully! Keep it secure.', 'success');
      closeModal('modal-security-settings');
      const warningBanner = document.getElementById('default-password-warning');
      if (warningBanner) warningBanner.style.display = 'none';
      State.isDefaultPassword = false;
    }
  } catch (err) {
    alertBox.textContent = err.message || 'Failed to change password.';
    alertBox.style.display = 'block';
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Update Password';
  }
}

async function submitUpdateProfile(e) {
  e.preventDefault();
  const alertBox = document.getElementById('profile-update-alert');
  const submitBtn = document.getElementById('btn-submit-profile');
  const username = document.getElementById('sec-username').value.trim();
  const full_name = document.getElementById('sec-fullname').value.trim();
  const email = document.getElementById('sec-email').value.trim();

  alertBox.style.display = 'none';
  submitBtn.disabled = true;
  submitBtn.textContent = 'Saving...';

  try {
    const res = await apiRequest('/api/auth/update-profile', {
      method: 'POST',
      body: { username, full_name, email }
    });

    if (res && res.success) {
      showToast('Profile updated successfully!', 'success');
      State.currentUser = res.user;
      document.getElementById('header-user-name').textContent = res.user.full_name || res.user.username;
      document.getElementById('header-user-avatar').textContent = (res.user.full_name || res.user.username).charAt(0).toUpperCase();
      closeModal('modal-security-settings');
    }
  } catch (err) {
    alertBox.textContent = err.message || 'Failed to update profile.';
    alertBox.style.display = 'block';
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = 'Save Profile';
  }
}

// Explicitly bind global administrative actions to window object
window.openRegisterStudentModal = openRegisterStudentModal;
window.submitStudentRegistration = submitStudentRegistration;
window.viewStudentDetails = viewStudentDetails;
window.openEditStudentModal = openEditStudentModal;
window.submitEditStudent = submitEditStudent;
window.openDeleteStudentModal = openDeleteStudentModal;
window.confirmPermanentDeleteStudent = confirmPermanentDeleteStudent;
window.confirmDeactivateStudent = confirmDeactivateStudent;
window.editStudentFromProfile = editStudentFromProfile;
window.deleteStudentFromProfile = deleteStudentFromProfile;
window.openAddStaffModal = openAddStaffModal;
window.submitAddStaff = submitAddStaff;
window.openDeleteStaffModal = openDeleteStaffModal;
window.confirmDeleteStaff = confirmDeleteStaff;
window.loadStudents = loadStudents;
window.loadStaff = loadStaff;
window.loadDashboard = loadDashboard;
window.navigateTo = navigateTo;
window.closeModal = closeModal;
window.openSecuritySettingsModal = openSecuritySettingsModal;
window.switchSecurityTab = switchSecurityTab;
window.submitChangePassword = submitChangePassword;
window.submitUpdateProfile = submitUpdateProfile;


