import FormControl from "@mui/material/FormControl";
import InputLabel from "@mui/material/InputLabel";
import MenuItem from "@mui/material/MenuItem";
import Select from "@mui/material/Select";
import React, { useEffect, useState } from "react";
// @ts-ignore
import { usePagination, useTable } from "react-table"; 

export interface CsvFile {
  name: string;
  data: Array<Record<string, any>>;
  description: string;
}

interface CsvViewerProps {
  files: CsvFile[];
  defaultFile?: string;
}

const CsvViewer = ({ files, defaultFile }: CsvViewerProps) => {
  const [selectedFile, setSelectedFile] = useState<string>(
    defaultFile || (files[0]?.name || "")
  );
  const [description, setDescription] = useState<string>("");
  const [columns, setColumns] = useState<any[]>([]);
  const [data, setData] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      const currentFile = files.find((f) => f.name === selectedFile);
      if (currentFile && currentFile.data.length > 0) {
        const headers = Object.keys(currentFile.data[0]);
        setColumns(
          headers.map((header) => ({
            Header: header,
            accessor: header,
          }))
        );
        setData(currentFile.data);
      }
      setDescription(currentFile?.description || "");
      setLoading(false);
    };

    loadData();
  }, [selectedFile, files]);

  const tableInstance = useTable(
    {
      columns,
      data,
      initialState: { pageIndex: 0 },
    },
    usePagination
  );

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    prepareRow,
    page,
    canPreviousPage,
    canNextPage,
    pageOptions,
    gotoPage,
    nextPage,
    previousPage,
    state: { pageIndex },
  } = tableInstance;

  return (
    <div className="h-full w-full flex flex-col">
      <div className="shrink-0 mb-4">
        <FormControl variant="outlined" fullWidth>
          <InputLabel id="file-select-label">Select File</InputLabel>
          <Select
            labelId="file-select-label"
            value={selectedFile}
            onChange={(e) => setSelectedFile(e.target.value)}
            label="Select File"
          >
            {files.map((file) => (
              <MenuItem key={file.name} value={file.name}>
                {file.name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </div>

      <div className="flex-1 min-h-0 w-full flex flex-col">
        {description.length > 0 && (
          <div className="bg-blue-50 border-l-4 border-blue-500 p-4 mb-4 text-gray-700 rounded-r-lg shadow-sm">
            <p className="italic text-sm leading-relaxed">{description}</p>
          </div>
        )}

        <div className="relative w-full h-full border border-gray-200 rounded-lg overflow-hidden">
          <div className="absolute inset-0 overflow-auto">
            <table {...getTableProps()} className="w-full border-collapse">
              <thead className="sticky top-0 z-10 bg-gray-50">
                {headerGroups.map((headerGroup: any) => (
                  <tr {...headerGroup.getHeaderGroupProps()}>
                    {headerGroup.headers.map((column: any) => (
                      <th
                        {...column.getHeaderProps()}
                        className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap border-b border-gray-200"
                      >
                        {column.render("Header")}
                      </th>
                    ))}
                  </tr>
                ))}
              </thead>
              <tbody {...getTableBodyProps()}>
                {page.map((row: any) => {
                  prepareRow(row);
                  return (
                    <tr {...row.getRowProps()}>
                      {row.cells.map((cell: any) => (
                        <td
                          {...cell.getCellProps()}
                          className="px-6 py-4 whitespace-nowrap text-sm text-gray-900 border-b border-gray-200"
                        >
                          {cell.render("Cell")}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        <div className="shrink-0 flex items-center justify-between gap-2 py-4">
          <div className="flex gap-2">
            <button
              onClick={() => gotoPage(0)}
              disabled={!canPreviousPage}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              {"<<"}
            </button>
            <button
              onClick={() => previousPage()}
              disabled={!canPreviousPage}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Previous
            </button>
            <button
              onClick={() => nextPage()}
              disabled={!canNextPage}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              Next
            </button>
            <button
              onClick={() => gotoPage(pageOptions.length - 1)}
              disabled={!canNextPage}
              className="px-3 py-1 border rounded disabled:opacity-50"
            >
              {">>"}
            </button>
          </div>
          <span className="text-sm">
            Page <strong>{pageIndex + 1}</strong> of{" "}
            <strong>{pageOptions.length}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};

export default CsvViewer;
