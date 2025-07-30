graph TB
    subgraph "Client Tier"
        A[Web Browser<br/>React + TypeScript]
    end
    
    subgraph "AWS VPC - Private Network"
        subgraph "Public Subnet"
            B[Load Balancer<br/>Application Load Balancer]
            C[Bastion Host<br/>Management Access]
        end
        
        subgraph "Private Subnet - Web Tier"
            D[Web Server<br/>Nginx + Gunicorn]
            E[Application Server<br/>Django + DRF]
        end
        
        subgraph "Private Subnet - Database Tier"
            F[Database<br/>RDS PostgreSQL]
            G[Cache<br/>Redis<br/>(Optional)]
        end
        
        subgraph "Storage"
            H[File Storage<br/>S3 Bucket<br/>(Private)]
        end
    end
    
    subgraph "External Services"
        I[CloudWatch<br/>Monitoring & Logs]
        J[SES<br/>Email Notifications]
        K[IAM<br/>Access Management]
    end
    
    subgraph "Development & CI/CD"
        L[GitHub Repository]
        M[GitHub Actions<br/>CI/CD Pipeline]
        N[ECR<br/>Container Registry]
    end
    
    %% Client connections
    A -->|HTTPS| B
    
    %% Load balancer connections
    B -->|HTTP| D
    
    %% Web server connections
    D -->|WSGI| E
    
    %% Application connections
    E -->|SQL| F
    E -->|Cache| G
    E -->|Files| H
    E -->|Logs| I
    E -->|Email| J
    
    %% Management access
    C -->|SSH| D
    C -->|SSH| E
    
    %% AWS services
    K -->|Policies| B
    K -->|Policies| D
    K -->|Policies| E
    K -->|Policies| F
    
    %% CI/CD flow
    L -->|Push| M
    M -->|Build & Test| N
    M -->|Deploy| E
    
    %% Security groups
    classDef publicSubnet fill:#e1f5fe
    classDef privateSubnet fill:#f3e5f5
    classDef database fill:#fff3e0
    classDef external fill:#e8f5e8
    classDef cicd fill:#fff8e1
    
    class B,C publicSubnet
    class D,E privateSubnet
    class F,G database
    class H,I,J,K external
    class L,M,N cicd