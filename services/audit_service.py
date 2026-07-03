
from typing import Optional, List, Dict, Any
from config.database import get_connection, row_to_dict


class AuditService:
    @staticmethod
    def log_event(
        user_id: Optional[int],
        action_code: int,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        action_details: Optional[str] = None
    ):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_logs (action_id, user_id, ip_address, user_agent, action_details)
            VALUES (?, ?, ?, ?, ?)
        """, (action_code, user_id, ip_address, user_agent, action_details))
        conn.commit()
        conn.close()

    @staticmethod
    def get_logs(user_id: Optional[int] = None, role: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()

        if role == 'Auditor':
            cursor.execute("""
                SELECT al.*, la.action_name 
                FROM audit_logs al 
                LEFT JOIN log_actions la ON al.action_id = la.action_id 
                ORDER BY al.created_at DESC
            """)
        elif user_id:
            cursor.execute("""
                SELECT al.*, la.action_name 
                FROM audit_logs al 
                LEFT JOIN log_actions la ON al.action_id = la.action_id 
                WHERE al.user_id = ? 
                ORDER BY al.created_at DESC
            """, (user_id,))
        else:
            return []

        logs = []
        for row in cursor.fetchall():
            logs.append(row_to_dict(cursor, row))

        conn.close()
        return logs

