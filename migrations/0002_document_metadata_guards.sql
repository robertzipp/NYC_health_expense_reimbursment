-- Guard document metadata invariants for the first vertical slice.
-- Document binaries remain out of scope; only metadata is persisted.
CREATE TRIGGER validate_claim_documents_insert
BEFORE INSERT ON claim_documents
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN instr(NEW.file_name, '/') > 0 OR instr(NEW.file_name, char(92)) > 0
        THEN RAISE(ABORT, 'claim_documents.file_name must not contain path separators')
    END;
    SELECT CASE
        WHEN NEW.checksum_sha256 IS NOT NULL
             AND (
                length(NEW.checksum_sha256) != 64
                OR NEW.checksum_sha256 GLOB '*[^0-9A-Fa-f]*'
             )
        THEN RAISE(ABORT, 'claim_documents.checksum_sha256 must be a 64-character hexadecimal SHA-256')
    END;
END;

CREATE TRIGGER validate_claim_documents_update
BEFORE UPDATE ON claim_documents
FOR EACH ROW
BEGIN
    SELECT CASE
        WHEN instr(NEW.file_name, '/') > 0 OR instr(NEW.file_name, char(92)) > 0
        THEN RAISE(ABORT, 'claim_documents.file_name must not contain path separators')
    END;
    SELECT CASE
        WHEN NEW.checksum_sha256 IS NOT NULL
             AND (
                length(NEW.checksum_sha256) != 64
                OR NEW.checksum_sha256 GLOB '*[^0-9A-Fa-f]*'
             )
        THEN RAISE(ABORT, 'claim_documents.checksum_sha256 must be a 64-character hexadecimal SHA-256')
    END;
END;
