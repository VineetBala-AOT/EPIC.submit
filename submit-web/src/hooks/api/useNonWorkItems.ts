import { queryOptions, useQuery } from "@tanstack/react-query";
import { QUERY_KEY } from "./constants";
import { NonWorkItemType } from "@/models/NonWorkItem";
import { submitRequest } from "@/utils/axiosUtils";

const getNonWorkItemsByProjectId = async (
  projectId: number,
): Promise<NonWorkItemType[]> => {
  return await submitRequest<NonWorkItemType[]>({
    method: "GET",
    url: `projects/${projectId}/non-work-items`,
  });
};

type UseGetNonWorkItemsByProjectIdParams = {
  projectId?: number;
  enabled?: boolean;
};

export const getNonWorkItemsByProjectIdQueryOptions = ({
  projectId,
  enabled = true,
}: UseGetNonWorkItemsByProjectIdParams) =>
  queryOptions({
    queryKey: [QUERY_KEY.NON_WORK_ITEMS, projectId],
    queryFn: () => getNonWorkItemsByProjectId(projectId!),
    staleTime: 5 * 60 * 1000,
    enabled: enabled && Boolean(projectId),
  });

/** Non-work item types (e.g. Management Plan) the project is eligible for. */
export const useGetNonWorkItemsByProjectId = ({
  projectId,
  enabled = true,
}: UseGetNonWorkItemsByProjectIdParams) => {
  return useQuery(getNonWorkItemsByProjectIdQueryOptions({ projectId, enabled }));
};
