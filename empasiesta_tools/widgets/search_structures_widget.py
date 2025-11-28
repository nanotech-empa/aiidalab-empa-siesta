import ipywidgets as ipw
from aiida.orm import StructureData, WorkChainNode, QueryBuilder
from datetime import datetime, timedelta
import base64
from empasiesta_tools import utils


VIEWERS = {
    "SIESTA_calc": "view_calc.ipynb",
}


class SearchStructuresWidget(ipw.VBox):
    """
    A widget for searching SIESTA_calc workchains in a date range
    and displaying them in an interactive HTML table.
    """

    def __init__(self):
        # ----------------------------------------------
        # Default dates: today and 7 days ago
        # ----------------------------------------------
        today = datetime.today().date()
        one_week_ago = today - timedelta(days=7)

        self.start_date = ipw.DatePicker(
            description="Start date",
            value=one_week_ago
        )

        self.end_date = ipw.DatePicker(
            description="End date",
            value=today
        )

        self.run_button = ipw.Button(
            description="Search",
            button_style="success"
        )

        self.output_area = ipw.Output()

        # connect callback
        self.run_button.on_click(self._on_search_clicked)

        # layout
        super().__init__([
            self.start_date,
            self.end_date,
            self.run_button,
            self.output_area
        ])

    # ------------------------------------------------------------------
    # Query method
    # ------------------------------------------------------------------
    def _find_finished_siesta_workchains(self, start, end):
        filters = {
            "label": "SIESTA_calc",
            "attributes.process_state": "finished",
            "attributes.exit_status": 0,
            "ctime": {
                "and": [
                    {"<=": end},
                    {">": start}
                ]
            }
        }

        qb = QueryBuilder()
        qb.append(WorkChainNode, filters=filters, project=["*"])
        return [wc[0] for wc in qb.all()]

    # ------------------------------------------------------------------
    # Thumbnail and table builder
    # ------------------------------------------------------------------
    def _build_workchain_table(self, workchains):
        html = """
        <table style="border-collapse: collapse; width: 100%;">
          <tr style="background-color: #e0e0e0;">
            <th style="border: 1px solid #aaa; padding: 6px;">Creation Time</th>
            <th style="border: 1px solid #aaa; padding: 6px;">Info</th>
            <th style="border: 1px solid #aaa; padding: 6px;">Input Structure</th>
          </tr>
        """

        for wc in workchains:

            # ---------------------- Column 1 ----------------------
            ctime_str = wc.ctime.strftime("%Y-%m-%d")

            # ---------------------- Column 2 ----------------------
            description = f"PK: {wc.pk} {wc.description}"
            wc_label = wc.label
            wc_pk = wc.pk

            # clickable description
            viewer = VIEWERS.get(wc_label, None)
            if viewer:
                desc_html = (
                    f'<a target="_blank" href="./{viewer}?pk={wc_pk}">'
                    f'{description}</a>'
                )
            else:
                desc_html = description

            info_lines = [desc_html]

            # FreeE
            try:
                free_e = wc.outputs.output_parameters.get_dict().get("FreeE")
                if free_e is not None:
                    info_lines.append(f"{free_e} eV")
            except Exception:
                pass

            # clickable output structure PK
            if "output_structure" in wc.outputs:
                out_struct = wc.outputs.output_structure
                out_pk = out_struct.pk
                out_html = (
                    f'<a target="_blank" href="./export_structure.ipynb?uuid={out_pk}">'
                    f'Equilibrium geometry PK: {out_pk}</a>'
                )
                info_lines.append(out_html)

            info_html = "<br>".join(info_lines)

            # ---------------------- Column 3 ----------------------
            structure = wc.inputs.structure
            struct_uuid = structure.uuid

            # retrieve or generate thumbnail
            if "thumbnail" not in structure.extras:
                thumb_bytes = utils.ase_to_thumbnail(structure=structure.get_ase())
                thumb_b64 = base64.b64encode(thumb_bytes).decode()
                structure.base.extras.set("thumbnail", thumb_b64)
            else:
                thumb = structure.extras["thumbnail"]
                if isinstance(thumb, bytes):
                    thumb_b64 = base64.b64encode(thumb).decode()
                elif isinstance(thumb, str):
                    thumb_b64 = thumb
                else:
                    thumb_bytes = utils.ase_to_thumbnail(structure=structure.get_ase())
                    thumb_b64 = base64.b64encode(thumb_bytes).decode()
                    structure.base.extras.set("thumbnail", thumb_b64)

            # clickable thumbnail
            image_html = (
                f'<a target="_blank" href="./export_structure.ipynb?uuid={struct_uuid}">'
                f'<img src="data:image/png;base64,{thumb_b64}" '
                f'style="max-height: 80px; cursor: pointer;" '
                f'title="Input structure PK: {structure.pk}"></a>'
            )

            # ---------------------- Row ----------------------
            html += f"""
            <tr>
              <td style="border: 1px solid #aaa; padding: 6px;">{ctime_str}</td>
              <td style="border: 1px solid #aaa; padding: 6px;">{info_html}</td>
              <td style="border: 1px solid #aaa; padding: 6px;">{image_html}</td>
            </tr>
            """

        html += "</table>"
        return ipw.HTML(value=html)

    # ------------------------------------------------------------------
    # Button callback
    # ------------------------------------------------------------------
    def _on_search_clicked(self, b):
        self.output_area.clear_output()

        start = datetime.combine(self.start_date.value, datetime.min.time())
        end = datetime.combine(self.end_date.value, datetime.max.time())

        with self.output_area:
            print(f"Querying from {start} to {end} …")
            wcs = self._find_finished_siesta_workchains(start, end)
            print(f"Found {len(wcs)} workchains:")

            table = self._build_workchain_table(wcs)
            display(table)