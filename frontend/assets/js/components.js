/* =============================================
   FortressVault - Reusable Components
   =============================================
   Contains: Sidebar, Navbar, Footer
   ============================================= */

const components = {
    getSidebar(currentPage) {
        const user = jwtUtils.getUser() || { role_name: 'User' };
        const role = user.role_name || 'User';
        
        let navLinks = '';
        if (role === 'Admin') {
            navLinks = `
                <a href="dashboard.html" class="nav-link ${currentPage === 'dashboard' ? 'active' : ''}">
                    <i class="fas fa-tachometer-alt"></i> Admin Dashboard
                </a>
                <a href="users.html" class="nav-link ${currentPage === 'users' ? 'active' : ''}">
                    <i class="fas fa-users"></i> Users Management
                </a>
                <a href="vault.html" class="nav-link ${currentPage === 'vault' ? 'active' : ''}">
                    <i class="fas fa-lock"></i> All Vaults (Encrypted)
                </a>
                <a href="audit-log.html" class="nav-link ${currentPage === 'audit-log' ? 'active' : ''}">
                    <i class="fas fa-history"></i> System Audit Log
                </a>
                <a href="benchmark.html" class="nav-link ${currentPage === 'benchmark' ? 'active' : ''}">
                    <i class="fas fa-chart-bar"></i> Benchmark
                </a>
                <hr class="my-2 mx-3 border-secondary opacity-25">
                <a href="profile.html" class="nav-link ${currentPage === 'profile' ? 'active' : ''}">
                    <i class="fas fa-user-shield"></i> Profile
                </a>
            `;
        } else if (role === 'Auditor') {
            navLinks = `
                <a href="audit-log.html" class="nav-link ${currentPage === 'audit-log' ? 'active' : ''}">
                    <i class="fas fa-history"></i> System Audit Log
                </a>
                <a href="dashboard.html" class="nav-link ${currentPage === 'dashboard' ? 'active' : ''}">
                    <i class="fas fa-tachometer-alt"></i> Auditor Dashboard
                </a>
                <hr class="my-2 mx-3 border-secondary opacity-25">
                <a href="profile.html" class="nav-link ${currentPage === 'profile' ? 'active' : ''}">
                    <i class="fas fa-user"></i> Profile
                </a>
            `;
        } else {
            navLinks = `
                <a href="vault.html" class="nav-link ${currentPage === 'vault' ? 'active' : ''}">
                    <i class="fas fa-key"></i> My Vault
                </a>
                <a href="add-vault.html" class="nav-link ${currentPage === 'add-vault' ? 'active' : ''}">
                    <i class="fas fa-plus-circle"></i> Add Vault
                </a>
                <a href="audit-log.html?mode=my-activity" class="nav-link ${currentPage === 'audit-log' ? 'active' : ''}">
                    <i class="fas fa-user-clock"></i> My Activity
                </a>
                <hr class="my-2 mx-3 border-secondary opacity-25">
                <a href="profile.html" class="nav-link ${currentPage === 'profile' ? 'active' : ''}">
                    <i class="fas fa-user"></i> Profile
                </a>
                <a href="settings.html" class="nav-link ${currentPage === 'settings' ? 'active' : ''}">
                    <i class="fas fa-cog"></i> Settings
                </a>
            `;
        }
        
        return `
            <div class="sidebar" id="sidebar">
                <div class="logo py-4 px-4 border-bottom border-secondary opacity-25">
                    <i class="fas fa-shield-alt text-primary me-2"></i>
                    <span class="text-white fw-bold fs-4">FortressVault</span>
                </div>
                
                <nav class="mt-3">
                    ${navLinks}
                </nav>
                
                <div class="position-absolute bottom-0 w-100 p-3">
                    <button class="btn btn-outline-danger w-100" onclick="handleLogout()">
                        <i class="fas fa-sign-out-alt me-2"></i> Logout
                    </button>
                </div>
            </div>
        `;
    },
    
    getNavbar() {
        const user = jwtUtils.getUser();
        return `
            <nav class="top-navbar d-flex justify-content-between align-items-center">
                <button class="btn btn-outline-secondary d-lg-none" id="toggle-sidebar">
                    <i class="fas fa-bars"></i>
                </button>
                
                <h5 class="mb-0 ms-2 d-none d-lg-block">Welcome, <strong>${user.username}</strong></h5>
                
                <div class="d-flex align-items-center gap-3">
                    <span class="badge bg-primary"><i class="fas fa-user-shield"></i> ${user.role_name}</span>
                </div>
            </nav>
        `;
    },
    
    getFooter() {
        return `
            <footer class="text-center py-3 border-top mt-auto">
                <p class="mb-0 text-muted small">&copy; ${new Date().getFullYear()} FortressVault. All rights reserved.</p>
            </footer>
        `;
    },
    
    load(currentPage) {
        document.getElementById('sidebar-container').innerHTML = this.getSidebar(currentPage);
        document.getElementById('navbar-container').innerHTML = this.getNavbar();
        document.getElementById('footer-container').innerHTML = this.getFooter();
        
        // Toggle sidebar for mobile
        const toggleBtn = document.getElementById('toggle-sidebar');
        if (toggleBtn) {
            toggleBtn.addEventListener('click', () => {
                document.getElementById('sidebar').classList.toggle('show');
            });
        }
    }
};

async function handleLogout() {
    try {
        await api.post('/api/auth/logout', {});
    } catch (e) {
        // Ignore
    }
    jwtUtils.logout();
    toastUtils.show('Logged out successfully', 'info');
}
