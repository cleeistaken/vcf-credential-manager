// Dashboard JavaScript functionality

let editingEnvironmentId = null;

// Load credential counts for all environments
document.addEventListener('DOMContentLoaded', function() {
    loadCredentialCounts();
});

async function loadCredentialCounts() {
    const cards = document.querySelectorAll('.environment-card');
    
    for (const card of cards) {
        const envId = card.dataset.envId;
        const countElement = document.getElementById(`cred-count-${envId}`);
        
        try {
            const response = await fetch(`/api/environments/${envId}/credentials`);
            const credentials = await response.json();
            countElement.textContent = `${credentials.length} credential${credentials.length !== 1 ? 's' : ''}`;
        } catch (error) {
            console.error(`Error loading credentials for environment ${envId}:`, error);
            countElement.textContent = 'Error loading';
        }
    }
}

function openAddEnvironmentModal() {
    editingEnvironmentId = null;
    document.getElementById('modal-title').textContent = 'Add Environment';
    document.getElementById('environmentForm').reset();
    document.getElementById('env-id').value = '';
    document.getElementById('installer-ssl-verify').checked = true;
    document.getElementById('manager-ssl-verify').checked = true;
    document.getElementById('installer-toggle').checked = false;
    document.getElementById('installer-section').style.display = 'none';
    document.getElementById('env-modal').classList.add('show');
}

function closeEnvironmentModal() {
    document.getElementById('env-modal').classList.remove('show');
    editingEnvironmentId = null;
}

function toggleInstallerSection() {
    const toggle = document.getElementById('installer-toggle');
    const section = document.getElementById('installer-section');
    section.style.display = toggle.checked ? 'block' : 'none';
}

async function editEnvironment(envId) {
    editingEnvironmentId = envId;
    document.getElementById('modal-title').textContent = 'Edit Environment';
    
    try {
        const response = await fetch(`/api/environments/${envId}`);
        const env = await response.json();
        
        document.getElementById('env-id').value = env.id;
        document.getElementById('env-name').value = env.name;
        document.getElementById('env-description').value = env.description || '';
        document.getElementById('installer-host').value = env.installer_host || '';
        document.getElementById('installer-username').value = env.installer_username || '';
        document.getElementById('installer-ssl-verify').checked = env.installer_ssl_verify !== false;
        document.getElementById('manager-host').value = env.manager_host || '';
        document.getElementById('manager-username').value = env.manager_username || '';
        document.getElementById('manager-ssl-verify').checked = env.manager_ssl_verify !== false;
        
        // Separate sync settings for installer and manager
        document.getElementById('installer-sync-enabled').checked = env.installer_sync_enabled || false;
        document.getElementById('installer-sync-interval').value = env.installer_sync_interval_minutes || 0;
        document.getElementById('manager-sync-enabled').checked = env.manager_sync_enabled !== false;
        document.getElementById('manager-sync-interval').value = env.manager_sync_interval_minutes || 60;
        
        // Show installer section if it has data
        const hasInstallerData = env.installer_host || env.installer_username;
        document.getElementById('installer-toggle').checked = hasInstallerData;
        document.getElementById('installer-section').style.display = hasInstallerData ? 'block' : 'none';
        
        document.getElementById('env-modal').classList.add('show');
    } catch (error) {
        console.error('Error loading environment:', error);
        alert('Failed to load environment details');
    }
}

async function saveEnvironment() {
    const form = document.getElementById('environmentForm');
    const formData = new FormData(form);
    
    const data = {
        name: formData.get('name'),
        description: formData.get('description'),
        installer_host: formData.get('installer_host'),
        installer_username: formData.get('installer_username'),
        installer_password: formData.get('installer_password'),
        installer_ssl_verify: document.getElementById('installer-ssl-verify').checked,
        manager_host: formData.get('manager_host'),
        manager_username: formData.get('manager_username'),
        manager_password: formData.get('manager_password'),
        manager_ssl_verify: document.getElementById('manager-ssl-verify').checked,
        // Separate sync settings for installer and manager
        installer_sync_enabled: document.getElementById('installer-sync-enabled').checked,
        installer_sync_interval_minutes: parseInt(formData.get('installer_sync_interval_minutes')) || 0,
        manager_sync_enabled: document.getElementById('manager-sync-enabled').checked,
        manager_sync_interval_minutes: parseInt(formData.get('manager_sync_interval_minutes')) || 60,
        ssl_verify: true  // Legacy field
    };
    
    // Validate
    if (!data.name) {
        alert('Environment name is required');
        return;
    }
    
    if (!data.installer_host && !data.manager_host) {
        alert('At least one of Installer Host or Manager Host must be specified');
        return;
    }
    
    try {
        let response;
        if (editingEnvironmentId) {
            // Update existing
            response = await fetch(`/api/environments/${editingEnvironmentId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        } else {
            // Create new
            response = await fetch('/api/environments', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
        }
        
        if (response.ok) {
            closeEnvironmentModal();
            location.reload();
        } else {
            const error = await response.json();
            alert(`Failed to save environment: ${error.error || 'Unknown error'}`);
        }
    } catch (error) {
        console.error('Error saving environment:', error);
        alert('Failed to save environment');
    }
}

async function deleteEnvironment(envId, envName) {
    // Enhanced confirmation prompt
    const confirmMessage = `⚠️ WARNING: Delete Environment?\n\n` +
        `Environment: "${envName}"\n\n` +
        `This action will:\n` +
        `• Delete the environment configuration\n` +
        `• Delete all associated credentials\n` +
        `• Stop any scheduled syncs\n\n` +
        `This action CANNOT be undone!\n\n` +
        `Type the environment name to confirm deletion:`;
    
    const userInput = prompt(confirmMessage);
    
    if (userInput === null) {
        // User clicked cancel
        return;
    }
    
    if (userInput !== envName) {
        alert(`Deletion cancelled. The entered name "${userInput}" does not match "${envName}".`);
        return;
    }
    
    try {
        const response = await fetch(`/api/environments/${envId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            alert(`Environment "${envName}" has been deleted successfully.`);
            location.reload();
        } else {
            alert('Failed to delete environment');
        }
    } catch (error) {
        console.error('Error deleting environment:', error);
        alert('Failed to delete environment');
    }
}

async function testCredentials() {
    const form = document.getElementById('environmentForm');
    const formData = new FormData(form);
    
    const data = {
        installer_host: formData.get('installer_host'),
        installer_username: formData.get('installer_username'),
        installer_password: formData.get('installer_password'),
        installer_ssl_verify: document.getElementById('installer-ssl-verify').checked,
        manager_host: formData.get('manager_host'),
        manager_username: formData.get('manager_username'),
        manager_password: formData.get('manager_password'),
        manager_ssl_verify: document.getElementById('manager-ssl-verify').checked
    };
    
    // Validate that at least one set of credentials is provided
    const hasInstaller = data.installer_host && data.installer_username && data.installer_password;
    const hasManager = data.manager_host && data.manager_username && data.manager_password;
    
    if (!hasInstaller && !hasManager) {
        alert('Please provide credentials for at least one system (Installer or Manager) to test.');
        return;
    }
    
    // Show loading state
    const testBtn = document.getElementById('test-btn');
    const originalText = testBtn.textContent;
    testBtn.textContent = '⏳ Testing...';
    testBtn.disabled = true;
    
    try {
        const response = await fetch('/api/test-credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        // Build result message
        let message = '🧪 Connection Test Results:\n\n';
        
        if (hasInstaller) {
            message += `VCF Installer (${data.installer_host}):\n`;
            if (result.results.installer.success) {
                message += `✅ ${result.results.installer.message}\n\n`;
            } else {
                message += `❌ ${result.results.installer.message}\n\n`;
            }
        }
        
        if (hasManager) {
            message += `SDDC Manager (${data.manager_host}):\n`;
            if (result.results.manager.success) {
                message += `✅ ${result.results.manager.message}\n\n`;
            } else {
                message += `❌ ${result.results.manager.message}\n\n`;
            }
        }
        
        if (result.success) {
            message += '✅ At least one connection succeeded. You can save this environment.';
        } else {
            message += '❌ All connections failed. Please check your credentials and try again.';
        }
        
        alert(message);
        
    } catch (error) {
        console.error('Error testing credentials:', error);
        alert('❌ Failed to test credentials. Please check the console for details.');
    } finally {
        testBtn.textContent = originalText;
        testBtn.disabled = false;
    }
}

async function syncEnvironment(envId) {
    if (!confirm('This will fetch the latest credentials from the VCF environment. Continue?')) {
        return;
    }
    
    const card = document.querySelector(`[data-env-id="${envId}"]`);
    const countElement = document.getElementById(`cred-count-${envId}`);
    countElement.textContent = 'Syncing...';
    
    try {
        const response = await fetch(`/api/environments/${envId}/sync`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (response.ok) {
            // Reload to get updated status including any errors
            location.reload();
        } else {
            // Still reload to show any partial results and error status
            location.reload();
        }
    } catch (error) {
        console.error('Error syncing environment:', error);
        // Reload to show current state
        location.reload();
    }
}

function viewEnvironment(envId) {
    window.location.href = `/environment/${envId}`;
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('env-modal');
    if (event.target === modal) {
        closeEnvironmentModal();
    }
}

// Close modal on Escape key
document.addEventListener('keydown', function(event) {
    if (event.key === 'Escape') {
        const modal = document.getElementById('env-modal');
        if (modal.classList.contains('show')) {
            closeEnvironmentModal();
        }
        const importModal = document.getElementById('import-modal');
        if (importModal.classList.contains('show')) {
            closeImportModal();
        }
    }
});

// Import Environment Functions
function openImportModal() {
    document.getElementById('import-file').value = '';
    document.getElementById('import-preview-section').style.display = 'none';
    document.getElementById('import-validation-section').style.display = 'none';
    document.getElementById('import-btn').disabled = true;
    document.getElementById('import-modal').classList.add('show');
}

function closeImportModal() {
    document.getElementById('import-modal').classList.remove('show');
}

async function previewImportFile() {
    const fileInput = document.getElementById('import-file');
    const previewSection = document.getElementById('import-preview-section');
    const previewElement = document.getElementById('import-preview');
    const importBtn = document.getElementById('import-btn');
    const validationSection = document.getElementById('import-validation-section');
    
    validationSection.style.display = 'none';
    
    if (!fileInput.files || !fileInput.files[0]) {
        previewSection.style.display = 'none';
        importBtn.disabled = true;
        return;
    }
    
    const file = fileInput.files[0];
    const reader = new FileReader();
    
    reader.onload = function(e) {
        const content = e.target.result;
        previewElement.textContent = content;
        previewSection.style.display = 'block';
        importBtn.disabled = false;
    };
    
    reader.onerror = function() {
        previewElement.textContent = 'Error reading file';
        previewSection.style.display = 'block';
        importBtn.disabled = true;
    };
    
    reader.readAsText(file);
}

async function validateAndImport() {
    const fileInput = document.getElementById('import-file');
    const importBtn = document.getElementById('import-btn');
    const validationSection = document.getElementById('import-validation-section');
    const validationResults = document.getElementById('import-validation-results');
    
    if (!fileInput.files || !fileInput.files[0]) {
        alert('Please select a file first');
        return;
    }
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);
    
    // Show loading state
    const originalText = importBtn.textContent;
    importBtn.textContent = '⏳ Validating...';
    importBtn.disabled = true;
    validationSection.style.display = 'none';
    
    try {
        const response = await fetch('/api/environments/import', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        // Show validation results
        validationSection.style.display = 'block';
        
        if (response.ok && result.success) {
            // Success - show results and close modal
            let html = '<div class="alert alert-success">';
            html += `<strong>✅ Environment "${result.environment.name}" created successfully!</strong><br><br>`;
            html += '<strong>Connection Test Results:</strong><br>';
            
            if (result.connection_tests.installer) {
                const test = result.connection_tests.installer;
                html += `• Installer: ${test.success ? '✅' : '❌'} ${test.message}<br>`;
            }
            if (result.connection_tests.manager) {
                const test = result.connection_tests.manager;
                html += `• Manager: ${test.success ? '✅' : '❌'} ${test.message}<br>`;
            }
            html += '</div>';
            
            validationResults.innerHTML = html;
            
            // Reload page after short delay
            setTimeout(() => {
                closeImportModal();
                location.reload();
            }, 2000);
            
        } else {
            // Error - show validation errors
            let html = '<div class="alert alert-danger">';
            html += `<strong>❌ Import Failed</strong><br><br>`;
            
            if (result.errors && result.errors.length > 0) {
                html += '<strong>Validation Errors:</strong><ul>';
                for (const error of result.errors) {
                    html += `<li>${error}</li>`;
                }
                html += '</ul>';
            }
            
            if (result.connection_tests) {
                html += '<strong>Connection Test Results:</strong><br>';
                if (result.connection_tests.installer) {
                    const test = result.connection_tests.installer;
                    html += `• Installer: ${test.success ? '✅' : '❌'} ${test.message}<br>`;
                }
                if (result.connection_tests.manager) {
                    const test = result.connection_tests.manager;
                    html += `• Manager: ${test.success ? '✅' : '❌'} ${test.message}<br>`;
                }
            }
            
            if (result.error) {
                html += `<br><strong>Error:</strong> ${result.error}`;
            }
            
            html += '</div>';
            validationResults.innerHTML = html;
            importBtn.disabled = false;
        }
        
    } catch (error) {
        console.error('Error importing environment:', error);
        validationSection.style.display = 'block';
        validationResults.innerHTML = `<div class="alert alert-danger">❌ Failed to import: ${error.message}</div>`;
        importBtn.disabled = false;
    } finally {
        importBtn.textContent = originalText;
    }
}

// Close import modal when clicking outside
window.addEventListener('click', function(event) {
    const importModal = document.getElementById('import-modal');
    if (event.target === importModal) {
        closeImportModal();
    }
});

