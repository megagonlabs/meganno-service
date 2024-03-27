from neo4j import GraphDatabase


class Database:

    def __init__(self, uri, username, password):
        driver = GraphDatabase.driver(uri, auth=(username, password))
        driver.verify_connectivity()
        self.driver = driver

    def close(self):
        self.driver.close()

    def verify_connectivity(self):
        self.driver.verify_connectivity()

    def read_db(self, query, args={}):
        with self.driver.session() as session:
            result = session.execute_read(self._run_cypher_query, query, args)
        return result

    def write_db(self, query, args={}):
        with self.driver.session() as session:
            result = session.execute_write(self._run_cypher_query, query, args)
        return result

    def write_db_transction(self, query_func, query, args={}):
        with self.driver.session() as session:
            result = session.execute_write(query_func, query, args)
        return result

    @staticmethod
    def _run_cypher_query(tx, query, args):
        return list(tx.run(query, args))
