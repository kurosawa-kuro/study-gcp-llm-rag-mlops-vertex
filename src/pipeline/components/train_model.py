from kfp import dsl


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "scikit-learn==1.3.2",
        "pandas==2.1.4",
        "pyarrow==14.0.2",
    ],
)
def train_model(
    X_train_in: dsl.Input[dsl.Dataset],
    y_train_in: dsl.Input[dsl.Dataset],
    n_estimators: int,
    max_depth: int,
    random_state: int,
    model_out: dsl.Output[dsl.Model],
):
    """RandomForestRegressor を構築・学習する。"""
    import pickle

    import pandas as pd
    from sklearn.ensemble import RandomForestRegressor

    X_train = pd.read_parquet(X_train_in.path)
    y_train = pd.read_parquet(y_train_in.path)["target"]

    model = RandomForestRegressor(
        n_estimators=n_estimators,
        max_depth=max_depth,
        random_state=random_state,
    )
    model.fit(X_train, y_train)

    with open(model_out.path, "wb") as f:
        pickle.dump(model, f)

    print(f"学習完了: n_estimators={n_estimators}, max_depth={max_depth}")
