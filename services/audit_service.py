
"""
Audit Service for FortressVault
Handles logging of all security events and actions
"""
from typing import Optional, List, Dict, Any
from config.database import execute_query, execute_non_query

class AuditService:
    @staticmethod
    def log_event(
        user_id: Optional[int],
        action_code: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        action_details: Optional[str] = None
    ) -> None:
        """
        Log an event to audit_logs table
        """
        execute_non_query("""
            INSERT INTO audit_logs (action_id, user_id, ip_address, user_agent, action_details, created_at)
            VALUES (?, ?, ?, ?, ?, GETDATE())
        """, (action_code, user_id, ip_address, user_agent, action_details))
    
    @staticmethod
    def get_logs(
        user_id: Optional[int] = None,
        role: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get audit logs based on role permissions
        - Auditor can see all logs
        - User can only see own logs
        - Admin can see all logs
        """
        if role == "Auditor" or role == "Admin":
            return execute_query("""
                SELECT TOP (?) al.audit_id, al.action_id, al.user_id, u.username, al.ip_address, al.user_agent, al.action_details, al.created_at, la.action_name, la.action_name as action
                FROM audit_logs al
                LEFT JOIN log_actions la ON al.action_id = la.action_id
                LEFT JOIN users u ON al.user_id = u.user_id
                ORDER BY al.created_at DESC
            """, (limit,))
        elif user_id:
            return execute_query("""
                SELECT TOP (?) al.audit_id, al.action_id, al.user_id, u.username, al.ip_address, al.user_agent, al.action_details, al.created_at, la.action_name, la.action_name as action
                FROM audit_logs al
                LEFT JOIN log_actions la ON al.action_id = la.action_id
                LEFT JOIN users u ON al.user_id = u.user_id
                WHERE al.user_id = ?
                ORDER BY al.created_at DESC
            """, (limit, user_id))
        return []

