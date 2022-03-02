
SQL_LIST_SCHEMATA = """select schema_name
		from information_schema.schemata
		where catalog_name = {}
		and schema_name in ({})"""

# SQL_LIST_HIBEDIT_CANDIDATES_ESRI = """select nome_tabela, 
# 	case  when editortracking_ativo then 'Sim'
# 	else 'Não'
# 	end as editortracking_ativo, 
# 	case when archiving_ativo then 'Sim'
# 	else 'Não'
# 	end as archiving_ativo, 
# 	case tipo_edicao 
# 		when 'HIBRIDA' then 'Híbrida'
# 		when 'SOMENTE_ESRI' then 'Apenas ESRI' 
# 		else '<em erro>' 
# 	end as tipo_edicao,
# 	num_registos,
# 	case when em_erro then 'Sim'
# 	else ''
# 	end as em_erro
#  from {0}.tabelas_esri_com_interesse($1)
#  order by nome_tabela"""

SQL_LIST_HIBEDIT_CANDIDATES = """select nome_tabela, 
	case  when editortracking_ativo then 'Sim'
	else 'Não'
	end as editortracking_ativo, 
	case when archiving_ativo then 'Sim'
	else 'Não'
	end as archiving_ativo, 
	case tipo_edicao 
		when 'HIBRIDA' then 'Híbrida'
		when 'SOMENTE_ESRI' then 'Apenas ESRI' 
		when 'SOMENTE_POSTGIS' then 'Apenas PostGIS/QGIS' 
		else '<em erro>' 
	end as tipo_edicao,
	num_registos,
	case when em_erro then 'Sim'
	else ''
	end as em_erro
 from {0}.tabelas_com_interesse($1)
 order by nome_tabela""" 

SQL_LIST_EXISTING_COLUMNS = """select column_name
	from information_schema.columns c
	where c.table_catalog = $1
	and c.table_schema = $2
	and c.table_name = $3
	and column_name not in 
		('objectid', 'shape', 'gdb_geomattr_data', 'gdb_archive_oid', 'created_user', 'created_date', 
		 'last_edited_user', 'last_edited_date', 'gdb_from_date', 'gdb_to_date')"""

SQL_LIST_EDITGRANTS = """select grantee
from
(
	SELECT grantee, array_Agg(privilege_type::text) privs
	FROM information_schema.role_table_grants 
	WHERE table_catalog = $1
	and table_schema = $2
	and table_name = $3
	group by grantee
) a
where 'INSERT' = ANY(a.privs) 
and 'UPDATE' = ANY(a.privs) 
and 'DELETE' = ANY(a.privs) 
and 'SELECT' = ANY(a.privs) 
ORDER BY grantee"""

SQL_THEME_ERROR_FLAGS = "select unnest(validar_tema_hibrido) from {0}.validar_tema_hibrido($1, $2)"

SQL_LIST_COL_CLASSES = "select distinct classe from {0}.t_campos_classe"

SQL_LIST_COL_CLASSES_RE = "select distinct classe from {0}.t_campos_classe where classe ~* $1"

SQL_ALTERAR_TEMA = "select {0}.tema_com_auditoria_historico($1, $2, $3, $4, $5)"
