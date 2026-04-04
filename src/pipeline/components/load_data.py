from kfp import dsl


@dsl.component(
    base_image="python:3.11-slim",
    packages_to_install=[
        "scikit-learn==1.3.2",
        "pandas==2.1.4",
        "pyarrow==14.0.2",
    ],
)
def load_data(
    test_size: float,
    random_state: int,
    X_train_out: dsl.Output[dsl.Dataset],
    X_test_out: dsl.Output[dsl.Dataset],
    y_train_out: dsl.Output[dsl.Dataset],
    y_test_out: dsl.Output[dsl.Dataset],
):
    """California Housing データセットを取得し train/test に分割する。"""
    import pandas as pd
    from sklearn.datasets import fetch_california_housing
    from sklearn.model_selection import train_test_split

    housing = fetch_california_housing(as_frame=True)
    X = housing.data
    y = housing.target

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )

    X_train.to_parquet(X_train_out.path)
    X_test.to_parquet(X_test_out.path)
    y_train.to_frame(name="target").to_parquet(y_train_out.path)
    y_test.to_frame(name="target").to_parquet(y_test_out.path)

    print(f"データ取得完了: train={len(X_train)}件, test={len(X_test)}件")
