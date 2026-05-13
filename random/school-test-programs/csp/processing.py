"""
processing.py — ML training pipeline, data loading, and Excel output utilities.

This module is the core of the CSP (Chemical Sensing Pipeline) ML workflow.
It trains multiple scikit-learn regressors on x/y data pairs, persists
trained models to disk as .pkl files, computes error metrics, and generates
Excel summaries and matplotlib scatter plots.

The expected data flow is:
    1. Load measurement data into a DataFrame via parse_data_file() (for .data files)
       or pd.read_csv() (for CSV files).
    2. Set x.label / y.label on the global DataAxis objects from model_def.
    3. Call process_main() to train, evaluate, and persist all models.

Typical usage:
    from model_def import x, y, ML_Model
    df = parse_data_file("It_measurement.data")   # current vs. time
    x.label = "Time"
    y.label = "Current"
    process_main(x, y, df, test_size=0.2, parentPath="./output", models=ML_Model.models)
"""

import pandas as pd
import os
import matplotlib.pyplot as plt
import openpyxl
import numpy as np
from model_def import *
import joblib
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def parse_data_file(path):
    """Parse a LabView .data file into a pandas DataFrame.

    The file format has a variable-length metadata header terminated by the
    sentinel line ``***End_of_Header***``.  The line immediately after the
    sentinel contains tab-separated column names.  Every subsequent non-empty
    line is a tab-separated row of floating-point values (scientific notation
    is supported, e.g. ``2.42E-7``).

    Two measurement types are supported:

    * **Current** files: columns are ``Time``, ``Current``
      (and optionally ``Filtered Current`` when present in the data).
    * **Voltage** files: columns are ``Time``, ``Voltage``
      (and optionally ``Filtered Voltage`` when present in the data).

    The number of column names used is determined by how many values actually
    appear in the data rows, so files where the header declares more columns
    than the data contains are handled gracefully.

    Args:
        path: Absolute or relative path to the ``.data`` file.

    Returns:
        pd.DataFrame with float64 columns named after the measurement headers.

    Raises:
        StopIteration: If ``***End_of_Header***`` is not found in the file.
        FileNotFoundError: If ``path`` does not exist.

    Example::

        df = parse_data_file("4_12_It.data")
        # df.columns -> Index(['Time', 'Current'], dtype='object')
    """
    with open(path, 'r') as f:
        lines = f.readlines()

    # Locate the header sentinel
    header_end_idx = next(
        i for i, line in enumerate(lines) if '***End_of_Header***' in line
    )

    # The line immediately after the sentinel lists the column names
    col_line = lines[header_end_idx + 1]
    declared_columns = [c.strip() for c in col_line.split('\t') if c.strip()]

    # Parse every subsequent non-empty line as a data row
    rows = []
    for line in lines[header_end_idx + 2:]:
        parts = [p.strip() for p in line.split('\t') if p.strip()]
        if not parts:
            continue
        try:
            rows.append([float(p) for p in parts])
        except ValueError:
            # Skip lines that cannot be parsed as numbers (should not occur
            # in well-formed files, but guards against stray text rows)
            continue

    if not rows:
        return pd.DataFrame(columns=declared_columns)

    # Use only as many column names as values are present in the data rows.
    # Some LabView exports declare a "Filtered" column in the header but omit
    # it from the actual data — this handles that mismatch silently.
    n_data_cols = len(rows[0])
    columns = declared_columns[:n_data_cols]

    return pd.DataFrame(rows, columns=columns)


# ---------------------------------------------------------------------------
# Core ML pipeline
# ---------------------------------------------------------------------------

def process_main(x, y, df, test_size, parentPath, models):
    """Train, evaluate, and persist all ML models on the given dataset.

    This is the main entry point for the regression pipeline.  It:

    1. Extracts the x and y column vectors from *df* and attaches them to the
       provided :class:`~model_def.DataAxis` objects.
    2. Splits the data into training and test sets (fixed ``random_state=10``
       for reproducibility).
    3. Fits every model in *models*, records R², MAE, MSE, and RMSE, and
       serialises the fitted model object to ``<parentPath>/models/<name>.pkl``.
    4. Writes an ``error-metrics.xlsx`` summary and an ``xy-data.xlsx`` file
       containing the original data alongside every model's test predictions.
    5. Saves three sets of scatter plots:
       - One ``<name>.jpg`` per model (original data + that model's predictions).
       - A single ``models.jpg`` grid showing all models in one figure.
       - A single ``total.jpg`` overlay of all models on one axes.

    Args:
        x: :class:`~model_def.DataAxis` instance for the independent variable.
           ``x.label`` must match a column name in *df*.
        y: :class:`~model_def.DataAxis` instance for the dependent variable.
           ``y.label`` must match a column name in *df*.
        df: DataFrame that contains at least the columns named by ``x.label``
            and ``y.label``.
        test_size: Fraction of the dataset to reserve for testing, e.g. ``0.2``
                   for an 80/20 train-test split.
        parentPath: Directory where all output files will be written.  Created
                    automatically if it does not yet exist.
        models: List of :class:`~model_def.ML_Model` instances to train.
    """
    # Populate the DataAxis objects from the DataFrame
    y.original = df[y.label]
    if x.label in df.columns:
        # Keep only the x column as a single-column DataFrame so that
        # train_test_split returns a 2-D array compatible with all estimators
        x.original = df.drop([col for col in df.columns if col != x.label], axis=1)

    x.train, x.test, y.train, y.test = train_test_split(
        x.original.values, y.original.values,
        test_size=test_size, random_state=10
    )

    # --- Train every model and record error metrics ---
    for model in models:
        try:
            model.model.fit(x.train, y.train)
        except Exception as e:
            print("Error at model.fit ", e)
        model.ypred = model.model.predict(x.test)
        model.r2   = r2_score(y.test, model.ypred)
        model.mse  = mean_squared_error(y.test, model.ypred)
        model.mae  = mean_absolute_error(y.test, model.ypred)
        model.rmse = np.sqrt(model.mse)

        # Persist the fitted model object so it can be reloaded by prediction.py
        modelsPath = os.path.join(parentPath, "models")
        if not os.path.exists(modelsPath):
            os.makedirs(modelsPath)
        joblib.dump(model, os.path.join(modelsPath, f"{model.name}.pkl"))

    # ------------------------------------------------------------------
    # Inner helpers — these close over x, y, models, and parentPath
    # ------------------------------------------------------------------

    def errorMetricsSheet(parentPath):
        """Write R², MAE, MSE, RMSE for every model to error-metrics.xlsx."""
        path = os.path.join(parentPath, 'error-metrics.xlsx')
        error_metrics = ML_Model.get_error_metrics(models)
        makeExcel(path, error_metrics)
        '''# Write the DataFrame to an Excel file
        with pd.ExcelWriter(path, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
            worksheet = writer.sheets["Sheet 1"]
            for column_cells in worksheet.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
            for row in worksheet.iter_rows():
                for cell in row:
                    cell.alignment = openpyxl.styles.Alignment(wrap_text=True)'''

    def putDataInCSV(parentPath):
        """Write x test values, original y values, and each model's predictions to xy-data.xlsx."""
        path = os.path.join(parentPath, 'xy-data.xlsx')
        y_preds = {
            f'{x.label}': x.test.flatten(),
            f'Original {y.label}': y.test.flatten()
        }
        for model in models:
            y_preds[model.name] = model.ypred.flatten()

        makeExcel(path, y_preds, f"Original {y.label}")

    def one_has_all(parentPath):
        """Save a grid figure with one subplot per model to models.jpg."""
        models_num = len(models)
        plt.figure(figsize=((models_num * 1.5) // 1, (models_num * 1.75) // 1))
        for i, model in enumerate(models):
            # Pick a grid layout that divides evenly; fall back to 3-column with
            # an extra row for awkward counts
            if models_num % 3 == 0:
                row_div, cols, add = 3, 3, 0
            elif models_num % 2 == 0:
                row_div, cols, add = 2, 2, 0
            elif models_num % 5 == 0:
                row_div, cols, add = 5, 5, 0
            else:
                row_div, cols, add = 3, 3, 1
            plt.subplot((models_num // row_div) + add, cols, i + 1)
            plotSingleModel(model, parentPath)
        plt.savefig(os.path.join(parentPath, f'models.jpg'))

    def singlePlots(parentPath):
        """Save one individual scatter-plot image per model."""
        for model in models:
            plotSingleModel(model, parentPath, save=True)

    def plotSingleModel(model, parentPath, save=False):
        """Scatter-plot original data (blue) and the model's test predictions (red).

        Args:
            model: Trained :class:`~model_def.ML_Model` instance.
            parentPath: Output directory for the saved image when *save* is True.
            save: When True, creates a new figure and saves it to disk.
                  When False, draws into the current active axes (used by
                  ``one_has_all`` to populate subplots).
        """
        if save:
            plt.figure(figsize=(10, 10))
        plt.scatter(x.original, y.original, color="blue")
        plt.scatter(x.test, model.ypred, color="red")
        plt.legend(["Orginial", model.name])
        plt.title(f"{model.name} Technique")
        plt.xlabel(x.label)
        plt.ylabel(y.label)
        if save:
            save_name = model.name.strip().replace(" ", "_").strip().lower()
            save_path = os.path.join(parentPath, f"{save_name}.jpg")
            plt.savefig(save_path)
            plt.close()

    def all_in_one(parentPath):
        """Save an overlay scatter plot with all models on a single axes to total.jpg."""
        plt.figure(figsize=(10, 10))
        plt.scatter(x.original, y.original, color="blue", label="Original")
        for color, model in zip(
            ('red', 'green', 'black', 'magenta', 'orange', 'violet',
             'brown', 'cyan', 'gray', 'khaki'),
            models
        ):
            plt.scatter(x.test, model.ypred, color=color, label=model.name)
        plt.legend()
        plt.xlabel(x.label)
        plt.ylabel(y.label)
        plt.title(f"{x.label} vs {y.label}")
        plt.savefig(os.path.join(parentPath, f"total.jpg"))

    # --- Execute all output steps ---
    errorMetricsSheet(parentPath)
    putDataInCSV(parentPath)
    singlePlots(parentPath)
    plt.close()
    one_has_all(parentPath)
    plt.close()
    all_in_one(parentPath)
    plt.close()


# ---------------------------------------------------------------------------
# Excel output utility
# ---------------------------------------------------------------------------

def makeExcel(path, data, sortby=None):
    """Write *data* to an Excel file with auto-fitted column widths.

    Args:
        path: Destination ``.xlsx`` file path.  Parent directory must exist.
        data: Either a ``dict`` mapping column names to lists of values, or an
              existing ``pd.DataFrame``.
        sortby: Optional column name to sort the rows by in ascending order
                before writing.  Pass ``None`` (default) to preserve order.
    """
    df = data if type(data) is pd.DataFrame else pd.DataFrame(data)

    if sortby:
        df.sort_values(by=[sortby], inplace=True)

    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
        worksheet = writer.sheets['Sheet1']
        # Auto-fit column widths based on the longest cell value in each column
        for column_cells in worksheet.columns:
            length = max(len(str(cell.value)) for cell in column_cells)
            worksheet.column_dimensions[column_cells[0].column_letter].width = length + 2
        for row in worksheet.iter_rows():
            for cell in row:
                cell.alignment = openpyxl.styles.Alignment(wrap_text=True)
