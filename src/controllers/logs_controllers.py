from datetime import datetime
from typing import List

from flask_sqlalchemy import SQLAlchemy

from src.models.log_model import LogModel


class LogsController:
    def __init__(
        self, 
        db: SQLAlchemy,
        model_plate,
    ):
        self.db = db
        self.model_plate = model_plate

    def create_log(
        self,
        ias: List[str],
        path: str = None,
        identifier: str = None,
        plate: str = None,
        thumbs: bool = False,
        start: datetime = datetime.now(),
        **kwargs,
    ):
        log = LogModel(
            ias=ias,
            identifier=identifier,
            plate=plate.upper(),
        )

        results = {}
        results['plate'] = self.model_plate.predict(path, thumbs)
        results['plate']['match'] = results['plate']['result'] == log.plate

        runtime = (datetime.now() - start).total_seconds()

        log.product = results['plate']['product']
        log.result = results
        log.runtime = runtime

        self.db.session.add(log)
        self.db.session.commit()

        return log

    def get_precision(self):
        results = {
            'plate': {
                'total': 0, 
                'match': 0, 
                'percent': 0,
            }
        }

        logs = self.db.session.query(LogModel).all()
        
        for log in logs:
            if 'plate' in log.ias:
                results['plate']['total'] += 1
                if log.match_plate:
                    results['plate']['match'] += 1

        try:
            results['plate']['percent'] = round(results['plate']['match'] / results['plate']['total'], 2) * 100
        except ZeroDivisionError:
            results['plate']['percent'] = 0

        return results

    
    def list_logs(self, page: int = 1) -> List[LogModel]:
        return (
            self.db.session
            .query(LogModel)
            .order_by(LogModel.created_at.desc())
            .paginate(page=int(page), per_page=15)
        )

    def list_all_logs(self) -> List[LogModel]:
        return (
            self.db.session
            .query(LogModel)
            .order_by(LogModel.created_at.desc())
            .all()
        )
