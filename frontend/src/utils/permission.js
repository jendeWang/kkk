const ROLE_PERMISSIONS = {
  admin: [
    'user:read', 'user:write', 'user:delete',
    'device:read', 'device:write', 'device:control', 'device:delete',
    'data:read', 'data:write', 'data:delete',
    'alert:read', 'alert:write', 'alert:delete',
    'rule:read', 'rule:write', 'rule:delete',
    'system:read', 'system:write',
  ],
  operator: [
    'device:read', 'device:write', 'device:control',
    'data:read', 'data:write',
    'alert:read', 'alert:write',
    'rule:read', 'rule:write',
    'user:read',
  ],
  viewer: [
    'device:read',
    'data:read',
    'alert:read',
    'rule:read',
    'user:read',
  ],
}

export function hasPermission(user, permission) {
  if (!user) return false
  if (user.is_superuser) return true
  const role = user.role || 'viewer'
  const permissions = ROLE_PERMISSIONS[role] || []
  return permissions.includes(permission)
}

export function hasAnyPermission(user, permissions) {
  return permissions.some(p => hasPermission(user, p))
}

export function getRoleName(role) {
  const names = {
    admin: '管理员',
    operator: '操作员',
    viewer: '查看员',
  }
  return names[role] || role || '查看员'
}

export function getRoleList() {
  return [
    { key: 'admin', name: '管理员', description: '拥有全部权限，可管理用户、设备、数据、规则等' },
    { key: 'operator', name: '操作员', description: '可操作设备、查看数据、配置告警和规则，不可管理用户' },
    { key: 'viewer', name: '查看员', description: '只能查看设备和数据，不可操作' },
  ]
}

export default {
  hasPermission,
  hasAnyPermission,
  getRoleName,
  getRoleList,
  ROLE_PERMISSIONS,
}
