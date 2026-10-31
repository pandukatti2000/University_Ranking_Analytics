import re
from typing import Tuple, Optional, Set
import sqlglot
from sqlglot import exp

APPROVED_TABLES: Set[str] = {
    "country",
    "ranking_system",
    "ranking_criteria",
    "university",
    "university_ranking_year",
    "university_year",
    "v_university_overview",
    "v_criteria_overview",
    "v_ranked_universities",
}

FORBIDDEN_KEYWORDS = [
    r"\bpg_sleep\b",
    r"\bpg_read_file\b",
    r"\bpg_write_file\b",
    r"\bversion\s*\(",
    r"\bcurrent_user\b",
    r"\bsystem_user\b",
    r"\binformation_schema\b",
    r"\bpg_catalog\b",
    r"\bpg_tables\b",
]

class SQLSafetyValidator:
    """
    AST-based SQL safety validator using SQLGlot.
    Enforces strict read-only semantics, table whitelisting,
    statement isolation, and row limits.
    """

    @classmethod
    def validate_and_sanitize(cls, sql_query: str, max_limit: int = 100) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Validates the SQL query.
        Returns:
            (is_valid, sanitized_sql_or_none, error_message_or_none)
        """
        if not sql_query or not sql_query.strip():
            return False, None, "Query is empty."

        cleaned_sql = sql_query.strip()
        # Remove trailing semicolons
        cleaned_sql = re.sub(r";+\s*$", "", cleaned_sql)

        # 1. Reject multiple statements (semicolon inside query)
        if ";" in cleaned_sql:
            return False, None, "Multiple SQL statements are strictly forbidden."

        # 2. Check for dangerous functions / system catalog access
        for pattern in FORBIDDEN_KEYWORDS:
            if re.search(pattern, cleaned_sql, re.IGNORECASE):
                return False, None, "Access to system catalogs, metadata tables, or sleep functions is prohibited."

        # 3. Parse AST using SQLGlot
        try:
            parsed = sqlglot.parse_one(cleaned_sql, read="postgres")
        except Exception as e:
            return False, None, f"SQL syntax error: {str(e)}"

        if not parsed:
            return False, None, "Unable to parse SQL query."

        # 4. Strict root expression check: must be a SELECT or UNION
        if not isinstance(parsed, (exp.Select, exp.Union)):
            return False, None, f"Query must be a SELECT statement. Detected forbidden expression: {type(parsed).__name__}"

        # 5. Check for any nested DML / DDL expressions
        forbidden_ast_nodes = (
            exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter,
            exp.Create, exp.Command, exp.TruncateTable, exp.SetItem
        )
        for node in parsed.walk():
            if isinstance(node, forbidden_ast_nodes):
                return False, None, f"Forbidden SQL operation detected: {type(node).__name__}"

        # 6. Validate table references
        tables_referenced = set()
        for table in parsed.find_all(exp.Table):
            t_name = table.name.lower()
            tables_referenced.add(t_name)
            if t_name not in APPROVED_TABLES:
                return False, None, f"Query references unapproved table or view: '{t_name}'. Only official ranking schema entities are permitted."

        if not tables_referenced:
            return False, None, "Query must reference at least one approved database table."

        # 7. Ensure LIMIT is present and capped
        limit_node = parsed.args.get("limit")
        if limit_node is None:
            parsed = parsed.limit(max_limit)
        else:
            try:
                curr_limit = int(limit_node.expression.this)
                if curr_limit > max_limit:
                    limit_node.set("expression", exp.Literal.number(max_limit))
            except Exception:
                limit_node.set("expression", exp.Literal.number(max_limit))

        sanitized_sql = parsed.sql(dialect="postgres")
        return True, sanitized_sql, None
