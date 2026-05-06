CREATE TABLE dbo.Claims (
    ClaimId UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_Claims PRIMARY KEY,
    AgencyId NVARCHAR(64) NOT NULL,
    EmployeeId NVARCHAR(64) NOT NULL,
    Status NVARCHAR(32) NOT NULL CONSTRAINT DF_Claims_Status DEFAULT ('Draft'),
    CreatedAtUtc DATETIME2(7) NOT NULL CONSTRAINT DF_Claims_CreatedAtUtc DEFAULT (SYSUTCDATETIME()),
    SubmittedAtUtc DATETIME2(7) NULL,
    CONSTRAINT CK_Claims_Status CHECK (Status IN ('Draft', 'Submitted')),
    CONSTRAINT CK_Claims_SubmittedAt CHECK ((Status = 'Draft' AND SubmittedAtUtc IS NULL) OR (Status = 'Submitted' AND SubmittedAtUtc IS NOT NULL))
);
GO

CREATE TABLE dbo.ClaimExpenses (
    ExpenseId UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_ClaimExpenses PRIMARY KEY,
    ClaimId UNIQUEIDENTIFIER NOT NULL,
    Claimant NVARCHAR(200) NOT NULL,
    DateOfService DATE NOT NULL,
    ExpenseCategory NVARCHAR(80) NOT NULL,
    AmountChargedCents INT NOT NULL,
    RequestedReimbursementCents INT NOT NULL,
    ServiceType NVARCHAR(80) NOT NULL,
    DocumentationRequired BIT NOT NULL CONSTRAINT DF_ClaimExpenses_DocumentationRequired DEFAULT (1),
    CreatedAtUtc DATETIME2(7) NOT NULL CONSTRAINT DF_ClaimExpenses_CreatedAtUtc DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT FK_ClaimExpenses_Claims FOREIGN KEY (ClaimId) REFERENCES dbo.Claims (ClaimId),
    CONSTRAINT CK_ClaimExpenses_AmountCharged CHECK (AmountChargedCents > 0),
    CONSTRAINT CK_ClaimExpenses_RequestedReimbursement CHECK (RequestedReimbursementCents > 0 AND RequestedReimbursementCents <= AmountChargedCents),
    CONSTRAINT CK_ClaimExpenses_Claimant CHECK (LEN(LTRIM(RTRIM(Claimant))) > 0),
    CONSTRAINT CK_ClaimExpenses_Category CHECK (LEN(LTRIM(RTRIM(ExpenseCategory))) > 0),
    CONSTRAINT CK_ClaimExpenses_ServiceType CHECK (LEN(LTRIM(RTRIM(ServiceType))) > 0)
);
GO

CREATE TABLE dbo.ClaimDocuments (
    DocumentId UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_ClaimDocuments PRIMARY KEY,
    ClaimId UNIQUEIDENTIFIER NOT NULL,
    ExpenseId UNIQUEIDENTIFIER NOT NULL,
    SavedReceiptId UNIQUEIDENTIFIER NULL,
    FileName NVARCHAR(255) NOT NULL,
    MimeType NVARCHAR(120) NOT NULL,
    SizeBytes BIGINT NOT NULL,
    ChecksumSha256 CHAR(64) NOT NULL,
    DocumentType NVARCHAR(80) NOT NULL,
    AttachedAtUtc DATETIME2(7) NOT NULL CONSTRAINT DF_ClaimDocuments_AttachedAtUtc DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT FK_ClaimDocuments_Claims FOREIGN KEY (ClaimId) REFERENCES dbo.Claims (ClaimId),
    CONSTRAINT FK_ClaimDocuments_ClaimExpenses FOREIGN KEY (ExpenseId) REFERENCES dbo.ClaimExpenses (ExpenseId),
    CONSTRAINT CK_ClaimDocuments_FileName CHECK (FileName NOT LIKE '%/%' AND FileName NOT LIKE '%\%' AND FileName NOT LIKE '%.exe'),
    CONSTRAINT CK_ClaimDocuments_MimeType CHECK (MimeType IN ('application/pdf', 'image/jpeg', 'image/png')),
    CONSTRAINT CK_ClaimDocuments_SizeBytes CHECK (SizeBytes > 0),
    CONSTRAINT CK_ClaimDocuments_ChecksumSha256 CHECK (ChecksumSha256 NOT LIKE '%[^0-9a-f]%'),
    CONSTRAINT CK_ClaimDocuments_DocumentType CHECK (LEN(LTRIM(RTRIM(DocumentType))) > 0)
);
GO

CREATE TABLE dbo.SavedReceipts (
    ReceiptId UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_SavedReceipts PRIMARY KEY,
    AgencyId NVARCHAR(64) NOT NULL,
    EmployeeId NVARCHAR(64) NOT NULL,
    FileName NVARCHAR(255) NOT NULL,
    MimeType NVARCHAR(120) NOT NULL,
    SizeBytes BIGINT NOT NULL,
    ChecksumSha256 CHAR(64) NOT NULL,
    DocumentType NVARCHAR(80) NOT NULL,
    Description NVARCHAR(500) NULL,
    Status NVARCHAR(32) NOT NULL CONSTRAINT DF_SavedReceipts_Status DEFAULT ('Available'),
    ClaimId UNIQUEIDENTIFIER NULL,
    ExpenseId UNIQUEIDENTIFIER NULL,
    CreatedAtUtc DATETIME2(7) NOT NULL CONSTRAINT DF_SavedReceipts_CreatedAtUtc DEFAULT (SYSUTCDATETIME()),
    UpdatedAtUtc DATETIME2(7) NOT NULL CONSTRAINT DF_SavedReceipts_UpdatedAtUtc DEFAULT (SYSUTCDATETIME()),
    AttachedAtUtc DATETIME2(7) NULL,
    ArchivedAtUtc DATETIME2(7) NULL,
    CONSTRAINT FK_SavedReceipts_Claims FOREIGN KEY (ClaimId) REFERENCES dbo.Claims (ClaimId),
    CONSTRAINT FK_SavedReceipts_ClaimExpenses FOREIGN KEY (ExpenseId) REFERENCES dbo.ClaimExpenses (ExpenseId),
    CONSTRAINT CK_SavedReceipts_FileName CHECK (FileName NOT LIKE '%/%' AND FileName NOT LIKE '%\%' AND FileName NOT LIKE '%.exe'),
    CONSTRAINT CK_SavedReceipts_MimeType CHECK (MimeType IN ('application/pdf', 'image/jpeg', 'image/png')),
    CONSTRAINT CK_SavedReceipts_SizeBytes CHECK (SizeBytes > 0),
    CONSTRAINT CK_SavedReceipts_ChecksumSha256 CHECK (ChecksumSha256 NOT LIKE '%[^0-9a-f]%'),
    CONSTRAINT CK_SavedReceipts_DocumentType CHECK (LEN(LTRIM(RTRIM(DocumentType))) > 0),
    CONSTRAINT CK_SavedReceipts_Status CHECK (Status IN ('Available', 'Attached', 'Archived')),
    CONSTRAINT CK_SavedReceipts_AttachedState CHECK ((Status = 'Attached' AND ClaimId IS NOT NULL AND ExpenseId IS NOT NULL AND AttachedAtUtc IS NOT NULL) OR (Status <> 'Attached' AND ClaimId IS NULL AND ExpenseId IS NULL AND AttachedAtUtc IS NULL)),
    CONSTRAINT CK_SavedReceipts_ArchivedState CHECK ((Status = 'Archived' AND ArchivedAtUtc IS NOT NULL) OR (Status <> 'Archived' AND ArchivedAtUtc IS NULL))
);
GO

CREATE TABLE dbo.AuditEvents (
    AuditEventId UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_AuditEvents PRIMARY KEY,
    EventType NVARCHAR(120) NOT NULL,
    Outcome NVARCHAR(32) NOT NULL,
    EntityType NVARCHAR(80) NOT NULL,
    EntityId UNIQUEIDENTIFIER NOT NULL,
    ActorType NVARCHAR(64) NOT NULL,
    ActorId NVARCHAR(128) NOT NULL,
    AgencyId NVARCHAR(64) NOT NULL,
    CorrelationId NVARCHAR(128) NULL,
    OccurredAtUtc DATETIME2(7) NOT NULL CONSTRAINT DF_AuditEvents_OccurredAtUtc DEFAULT (SYSUTCDATETIME()),
    CONSTRAINT CK_AuditEvents_EventType CHECK (EventType IN ('claim.created', 'claim_expense.added', 'claim_document.attached', 'claim.submitted', 'claim.validation_failed', 'receipt.created', 'receipt.updated', 'receipt.archived', 'receipt.attached')),
    CONSTRAINT CK_AuditEvents_Outcome CHECK (Outcome IN ('success', 'failure'))
);
GO

CREATE INDEX IX_Claims_Employee ON dbo.Claims (AgencyId, EmployeeId, Status);
GO
CREATE INDEX IX_ClaimExpenses_Claim ON dbo.ClaimExpenses (ClaimId, CreatedAtUtc);
GO
CREATE INDEX IX_ClaimDocuments_Expense ON dbo.ClaimDocuments (ExpenseId, AttachedAtUtc);
GO
CREATE INDEX IX_SavedReceipts_Employee ON dbo.SavedReceipts (AgencyId, EmployeeId, Status, CreatedAtUtc);
GO
CREATE INDEX IX_AuditEvents_Entity ON dbo.AuditEvents (EntityType, EntityId, OccurredAtUtc);
GO
