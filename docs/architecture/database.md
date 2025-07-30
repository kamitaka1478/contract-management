erDiagram
    USERS {
        int id PK
        string username UK
        string email UK
        string password_hash
        string first_name
        string last_name
        boolean is_active
        boolean is_staff
        datetime created_at
        datetime updated_at
    }
    
    CONTRACTS {
        int id PK
        string contract_number UK
        string contract_name
        string contractor_name
        string contractor_email
        string contractor_phone
        date contract_start_date
        date contract_end_date
        decimal contract_amount
        string billing_cycle
        text contract_description
        string contract_status
        int created_by FK
        datetime created_at
        datetime updated_at
    }
    
    BILLING_RECORDS {
        int id PK
        int contract_id FK
        string billing_number UK
        date billing_date
        date due_date
        decimal billing_amount
        decimal tax_amount
        decimal total_amount
        string billing_status
        text billing_description
        int created_by FK
        datetime created_at
        datetime updated_at
    }
    
    MATCHING_RESULTS {
        int id PK
        int contract_id FK
        int billing_record_id FK
        string matching_status
        text discrepancy_details
        decimal amount_difference
        boolean is_resolved
        int resolved_by FK
        datetime resolved_at
        datetime created_at
        datetime updated_at
    }
    
    ALERTS {
        int id PK
        int contract_id FK
        int billing_record_id FK
        int matching_result_id FK
        string alert_type
        string alert_level
        string alert_title
        text alert_message
        boolean is_read
        boolean is_resolved
        int assigned_to FK
        datetime created_at
        datetime updated_at
    }
    
    CONTRACT_FILES {
        int id PK
        int contract_id FK
        string file_name
        string file_path
        string file_type
        int file_size
        string uploaded_by FK
        datetime uploaded_at
    }
    
    BILLING_FILES {
        int id PK
        int billing_record_id FK
        string file_name
        string file_path
        string file_type
        int file_size
        string uploaded_by FK
        datetime uploaded_at
    }
    
    AUDIT_LOGS {
        int id PK
        int user_id FK
        string action_type
        string table_name
        int record_id
        json old_values
        json new_values
        string ip_address
        string user_agent
        datetime created_at
    }
    
    %% Relationships
    USERS ||--o{ CONTRACTS : "created_by"
    USERS ||--o{ BILLING_RECORDS : "created_by"
    USERS ||--o{ MATCHING_RESULTS : "resolved_by"
    USERS ||--o{ ALERTS : "assigned_to"
    USERS ||--o{ CONTRACT_FILES : "uploaded_by"
    USERS ||--o{ BILLING_FILES : "uploaded_by"
    USERS ||--o{ AUDIT_LOGS : "user_id"
    
    CONTRACTS ||--o{ BILLING_RECORDS : "contract_id"
    CONTRACTS ||--o{ MATCHING_RESULTS : "contract_id"
    CONTRACTS ||--o{ ALERTS : "contract_id"
    CONTRACTS ||--o{ CONTRACT_FILES : "contract_id"
    
    BILLING_RECORDS ||--o{ MATCHING_RESULTS : "billing_record_id"
    BILLING_RECORDS ||--o{ ALERTS : "billing_record_id"
    BILLING_RECORDS ||--o{ BILLING_FILES : "billing_record_id"
    
    MATCHING_RESULTS ||--o{ ALERTS : "matching_result_id"